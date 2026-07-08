"""Raw-text operation prediction and executable routing baselines."""

from __future__ import annotations

import hashlib
import math
import random
import re
from collections import Counter

import numpy as np

from .executable_executor import ACTION_COST
from .executable_models import ExecutablePolicy, ExecutableTask
from .models import RouteAction, RoutePlan, Workload


SUPPORT_ACTIONS = (
    RouteAction.DECOMPOSE,
    RouteAction.USE_TOOL,
    RouteAction.EXECUTE_CODE,
    RouteAction.DELEGATE,
    RouteAction.VERIFY,
)

_ACTION_ORDER = {action: index for index, action in enumerate(SUPPORT_ACTIONS)}


def _features(text: str, use_character_features: bool = True) -> set[str]:
    normalized = " ".join(re.findall(r"[a-z0-9]+", text.lower()))
    words = normalized.split()
    features = set(words)
    features.update(f"{first}_{second}" for first, second in zip(words, words[1:]))
    if use_character_features:
        padded = f" {normalized} "
        for size in (3, 4, 5):
            features.update(
                f"c:{padded[index:index + size]}"
                for index in range(len(padded) - size + 1)
            )
    return features


def _sigmoid(value: float) -> float:
    if value >= 0:
        factor = math.exp(-value)
        return 1.0 / (1.0 + factor)
    factor = math.exp(value)
    return factor / (1.0 + factor)


class CalibratedTextOperationModel:
    """Independent logistic heads with dev-set temperature scaling."""

    def __init__(
        self,
        min_document_frequency: int = 2,
        use_character_features: bool = True,
    ) -> None:
        self.min_document_frequency = min_document_frequency
        self.use_character_features = use_character_features
        self.vocabulary: set[str] = set()
        self.feature_index: dict[str, int] = {}
        self.biases: dict[RouteAction, float] = {}
        self.weights: dict[RouteAction, np.ndarray] = {}
        self.temperatures: dict[RouteAction, float] = {}

    def fit(
        self,
        train_tasks: list[ExecutableTask],
        calibration_tasks: list[ExecutableTask],
    ) -> "CalibratedTextOperationModel":
        if not train_tasks or not calibration_tasks:
            raise ValueError("training and calibration tasks are required")
        document_frequency: Counter[str] = Counter()
        tokenized: list[set[str]] = []
        for task in train_tasks:
            task_tokens = self._extract(task.prompt)
            tokenized.append(task_tokens)
            document_frequency.update(task_tokens)
        self.vocabulary = {
            token
            for token, count in document_frequency.items()
            if count >= self.min_document_frequency
        }
        self.feature_index = {
            feature: index for index, feature in enumerate(sorted(self.vocabulary))
        }
        matrix = np.zeros((len(train_tasks), len(self.feature_index)), dtype=np.float64)
        for row, task_features in enumerate(tokenized):
            for feature in task_features & self.vocabulary:
                matrix[row, self.feature_index[feature]] = 1.0
        total = len(train_tasks)
        for action in SUPPORT_ACTIONS:
            labels = np.asarray(
                [float(action in task.required_actions) for task in train_tasks]
            )
            positives = int(labels.sum())
            negatives = total - positives
            if positives == 0 or negatives == 0:
                raise ValueError(f"action {action.value} needs both label classes")
            sample_weights = np.where(
                labels == 1.0,
                total / (2.0 * positives),
                total / (2.0 * negatives),
            )
            weights = np.zeros(len(self.feature_index), dtype=np.float64)
            bias = math.log(positives / negatives)
            learning_rate = 0.35
            regularization = 0.002
            for epoch in range(500):
                logits = np.clip(matrix @ weights + bias, -30.0, 30.0)
                probabilities = 1.0 / (1.0 + np.exp(-logits))
                errors = (probabilities - labels) * sample_weights / total
                rate = learning_rate / math.sqrt(1.0 + epoch / 50.0)
                weights -= rate * (matrix.T @ errors + regularization * weights)
                bias -= rate * float(errors.sum())
            self.biases[action] = bias
            self.weights[action] = weights

        candidate_temperatures = (0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0, 8.0)
        for action in SUPPORT_ACTIONS:
            logits = [self._logit(task.prompt, action) for task in calibration_tasks]
            labels = [float(action in task.required_actions) for task in calibration_tasks]
            self.temperatures[action] = min(
                candidate_temperatures,
                key=lambda temperature: sum(
                    (_sigmoid(logit / temperature) - label) ** 2
                    for logit, label in zip(logits, labels)
                ),
            )
        return self

    def _logit(self, text: str, action: RouteAction) -> float:
        if action not in self.biases:
            raise ValueError("model must be fit before prediction")
        return self.biases[action] + sum(
            self.weights[action][self.feature_index[feature]]
            for feature in self._extract(text)
            if feature in self.feature_index
        )

    def _extract(self, text: str) -> set[str]:
        return _features(text, use_character_features=self.use_character_features)

    def predict_proba(self, text: str) -> dict[RouteAction, float]:
        return {
            action: _sigmoid(self._logit(text, action) / self.temperatures[action])
            for action in SUPPORT_ACTIONS
        }

    def calibration_report(
        self, tasks: list[ExecutableTask]
    ) -> dict[str, dict[str, float]]:
        report: dict[str, dict[str, float]] = {}
        for action in SUPPORT_ACTIONS:
            probabilities = [self.predict_proba(task.prompt)[action] for task in tasks]
            labels = [float(action in task.required_actions) for task in tasks]
            brier = sum(
                (probability - label) ** 2
                for probability, label in zip(probabilities, labels)
            ) / len(tasks)
            report[action.value] = {
                "brier": brier,
                "temperature": self.temperatures[action],
                "positive_rate": sum(labels) / len(labels),
            }
        return report


def _ordered(actions: list[RouteAction]) -> tuple[RouteAction, ...]:
    return tuple(sorted(actions, key=_ACTION_ORDER.__getitem__))


class DirectPolicy(ExecutablePolicy):
    name = "direct"

    def route(self, task: ExecutableTask) -> RoutePlan:
        del task
        return RoutePlan(actions=(RouteAction.ANSWER,), rationale="answer directly")


class FixedAgentPolicy(ExecutablePolicy):
    name = "fixed_agent"

    def route(self, task: ExecutableTask) -> RoutePlan:
        del task
        return RoutePlan(
            actions=(*SUPPORT_ACTIONS, RouteAction.ANSWER),
            rationale="fixed full workflow",
        )


class StaticExecutablePolicy(ExecutablePolicy):
    name = "static_workload"

    def route(self, task: ExecutableTask) -> RoutePlan:
        if task.workload == Workload.DATA_ANALYSIS:
            actions = (RouteAction.DECOMPOSE, RouteAction.EXECUTE_CODE)
        elif task.workload == Workload.RESEARCH:
            actions = (RouteAction.DECOMPOSE, RouteAction.USE_TOOL, RouteAction.VERIFY)
        else:
            actions = (
                RouteAction.DECOMPOSE,
                RouteAction.USE_TOOL,
                RouteAction.EXECUTE_CODE,
                RouteAction.DELEGATE,
                RouteAction.VERIFY,
            )
        return RoutePlan(
            actions=(*actions, RouteAction.ANSWER),
            confidence=0.6,
            rationale="workload-specific fixed route",
        )


class KeywordPolicy(ExecutablePolicy):
    name = "keyword"

    _patterns = {
        RouteAction.DECOMPOSE: ("first", "separate", "intermediate", "two-link", "plan"),
        RouteAction.USE_TOOL: ("archive", "source", "retrieve", "extract", "parse", "document"),
        RouteAction.EXECUTE_CODE: ("calculate", "compute", "sum", "mean", "aggregate", "audit"),
        RouteAction.DELEGATE: ("delegate", "specialist", "outage", "offline", "locale"),
        RouteAction.VERIFY: ("verify", "check", "latest", "conflict", "reconcile", "validate"),
    }

    def route(self, task: ExecutableTask) -> RoutePlan:
        text = task.prompt.lower()
        actions = [
            action
            for action, patterns in self._patterns.items()
            if any(pattern in text for pattern in patterns)
        ]
        return RoutePlan(
            actions=(*_ordered(actions), RouteAction.ANSWER),
            confidence=0.65,
            rationale="raw-text keyword rules",
        )


class RandomExecutablePolicy(ExecutablePolicy):
    name = "random"

    def route(self, task: ExecutableTask) -> RoutePlan:
        digest = hashlib.sha256(task.task_id.encode("utf-8")).hexdigest()
        rng = random.Random(int(digest[:16], 16))
        count = rng.randint(0, 3)
        actions = _ordered(rng.sample(list(SUPPORT_ACTIONS), count))
        return RoutePlan(
            actions=(*actions, RouteAction.ANSWER),
            rationale="deterministic random route",
        )


class LearnedOneShotPolicy(ExecutablePolicy):
    name = "learned_one_shot"

    def __init__(self, model: CalibratedTextOperationModel) -> None:
        self.model = model

    def route(self, task: ExecutableTask) -> RoutePlan:
        probabilities = self.model.predict_proba(task.prompt)
        action, confidence = max(probabilities.items(), key=lambda item: item[1])
        actions = (action,) if confidence >= 0.5 else ()
        return RoutePlan(
            actions=(*actions, RouteAction.ANSWER),
            confidence=confidence,
            rationale="highest calibrated raw-text operation probability",
        )


class LearnedBudgetPolicy(ExecutablePolicy):
    def __init__(
        self,
        model: CalibratedTextOperationModel,
        threshold: float = 0.5,
        max_actions: int = 3,
        name: str = "learned_budget",
        enforce_budget: bool = True,
    ) -> None:
        self.model = model
        self.threshold = threshold
        self.max_actions = max_actions
        self.name = name
        self.enforce_budget = enforce_budget

    def route(self, task: ExecutableTask) -> RoutePlan:
        probabilities = self.model.predict_proba(task.prompt)
        candidates = sorted(
            (
                (action, probability)
                for action, probability in probabilities.items()
                if probability >= self.threshold
            ),
            key=lambda item: ((item[1] - self.threshold) / ACTION_COST[item[0]]),
            reverse=True,
        )
        selected: list[RouteAction] = []
        cost = ACTION_COST[RouteAction.ANSWER]
        for action, _probability in candidates:
            if len(selected) >= self.max_actions:
                break
            if not self.enforce_budget or cost + ACTION_COST[action] <= task.cost_budget:
                selected.append(action)
                cost += ACTION_COST[action]
        confidence = (
            sum(probabilities[action] for action in selected) / len(selected)
            if selected
            else 1.0 - max(probabilities.values())
        )
        return RoutePlan(
            actions=(*_ordered(selected), RouteAction.ANSWER),
            confidence=confidence,
            rationale="calibrated text predictions composed under action and cost budgets",
        )


class OraclePolicy(ExecutablePolicy):
    name = "oracle"

    def route(self, task: ExecutableTask) -> RoutePlan:
        return RoutePlan(
            actions=(*task.required_actions, RouteAction.ANSWER),
            confidence=1.0,
            rationale="minimum task annotation route",
        )


def tune_threshold(
    model: CalibratedTextOperationModel,
    dev_tasks: list[ExecutableTask],
) -> float:
    """Select a threshold on dev labels using exact routes, then macro action F1."""
    candidates = (0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70)

    def score(threshold: float) -> tuple[float, float, float]:
        policy = LearnedBudgetPolicy(model, threshold=threshold)
        exact = 0
        true_positive = false_positive = false_negative = 0
        total_cost = 0.0
        for task in dev_tasks:
            plan = policy.route(task)
            predicted = set(plan.actions) - {RouteAction.ANSWER}
            required = set(task.required_actions)
            exact += predicted == required
            true_positive += len(predicted & required)
            false_positive += len(predicted - required)
            false_negative += len(required - predicted)
            total_cost += sum(ACTION_COST[action] for action in plan.actions)
        denominator = 2 * true_positive + false_positive + false_negative
        f1 = 2 * true_positive / denominator if denominator else 1.0
        return exact / len(dev_tasks), f1, -total_cost / len(dev_tasks)

    return max(candidates, key=score)


def executable_policies(
    train_tasks: list[ExecutableTask],
    dev_tasks: list[ExecutableTask],
) -> tuple[list[ExecutablePolicy], CalibratedTextOperationModel, float]:
    model = CalibratedTextOperationModel().fit(train_tasks, dev_tasks)
    threshold = tune_threshold(model, dev_tasks)
    policies: list[ExecutablePolicy] = [
        DirectPolicy(),
        RandomExecutablePolicy(),
        FixedAgentPolicy(),
        StaticExecutablePolicy(),
        KeywordPolicy(),
        LearnedOneShotPolicy(model),
        LearnedBudgetPolicy(model, threshold=threshold),
        OraclePolicy(),
    ]
    return policies, model, threshold
