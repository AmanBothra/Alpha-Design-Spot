"""
Advanced Sentry monitoring and tracking utilities for Alpha Design Spot.
Provides enhanced error grouping, release tracking, and custom fingerprinting.
"""

import hashlib
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

import sentry_sdk
from sentry_sdk import configure_scope, set_context, set_tag, add_breadcrumb
from django.conf import settings


class SentryReleaseTracker:
    """
    Manages release tracking and deployment monitoring for Sentry.
    """

    @staticmethod
    def set_release_context(release_version: str, deployment_env: str = None):
        """
        Set release context for all Sentry events.

        Args:
            release_version: Version string for the current release
            deployment_env: Deployment environment (staging, production, etc.)
        """
        with configure_scope() as scope:
            scope.set_tag("release_version", release_version)
            if deployment_env:
                scope.set_tag("deployment_env", deployment_env)

            # Set release context
            set_context(
                "release",
                {
                    "version": release_version,
                    "deployment_env": deployment_env,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

    @staticmethod
    def track_feature_rollout(
        feature_name: str, rollout_percentage: float, user_id: str = None
    ):
        """
        Track feature rollouts and A/B tests.

        Args:
            feature_name: Name of the feature being rolled out
            rollout_percentage: Percentage of users with access (0-100)
            user_id: User ID for personalized tracking
        """
        set_tag("feature_rollout", feature_name)
        set_tag("rollout_percentage", str(rollout_percentage))

        set_context(
            "feature_rollout",
            {
                "feature_name": feature_name,
                "rollout_percentage": rollout_percentage,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )


class SentryErrorGrouping:
    """
    Provides custom error grouping and fingerprinting for better error organization.
    """

    @staticmethod
    def create_custom_fingerprint(
        error_type: str,
        module: str,
        operation: str,
        additional_context: Optional[Dict] = None,
    ) -> List[str]:
        """
        Create custom fingerprint for error grouping.

        Args:
            error_type: Type of error (validation, database, api, etc.)
            module: Module where error occurred
            operation: Operation being performed
            additional_context: Additional context for fingerprinting

        Returns:
            List of fingerprint components
        """
        fingerprint_base = [error_type, module, operation]

        if additional_context:
            # Create stable hash from context for consistent grouping
            context_hash = hashlib.md5(
                json.dumps(additional_context, sort_keys=True).encode()
            ).hexdigest()[:8]
            fingerprint_base.append(context_hash)

        return fingerprint_base

    @staticmethod
    def set_error_fingerprint(
        error_type: str,
        module: str,
        operation: str,
        additional_context: Optional[Dict] = None,
    ):
        """
        Set custom fingerprint for current error context.
        """
        fingerprint = SentryErrorGrouping.create_custom_fingerprint(
            error_type, module, operation, additional_context
        )

        with configure_scope() as scope:
            scope.fingerprint = fingerprint

    @staticmethod
    def group_by_user_action(action: str, resource: str, user_type: str = None):
        """
        Group errors by user actions for better UX insights.

        Args:
            action: User action (create, update, delete, view, etc.)
            resource: Resource being acted upon (post, user, event, etc.)
            user_type: Type of user (customer, admin, etc.)
        """
        fingerprint = ["user_action", action, resource]
        if user_type:
            fingerprint.append(user_type)

        with configure_scope() as scope:
            scope.fingerprint = fingerprint

        set_tag("user_action", action)
        set_tag("resource", resource)
        if user_type:
            set_tag("user_type", user_type)


class SentryUserJourney:
    """
    Tracks user journeys and workflows for better error context.
    """

    def __init__(self):
        self.journey_steps = []

    def start_journey(self, journey_name: str, user_id: str = None):
        """
        Start tracking a user journey.

        Args:
            journey_name: Name of the journey (registration, post_creation, etc.)
            user_id: User ID for personalized tracking
        """
        self.journey_steps = []

        set_context(
            "user_journey",
            {
                "journey_name": journey_name,
                "user_id": user_id,
                "started_at": datetime.utcnow().isoformat(),
                "steps": [],
            },
        )

        set_tag("journey_name", journey_name)
        if user_id:
            set_tag("journey_user_id", user_id)

        add_breadcrumb(
            message=f"Started user journey: {journey_name}",
            category="user_journey",
            level="info",
            data={"journey_name": journey_name, "user_id": user_id},
        )

    def add_step(self, step_name: str, step_data: Optional[Dict] = None):
        """
        Add a step to the current user journey.

        Args:
            step_name: Name of the step
            step_data: Additional data for the step
        """
        step = {
            "step_name": step_name,
            "timestamp": datetime.utcnow().isoformat(),
            "data": step_data or {},
        }

        self.journey_steps.append(step)

        # Update Sentry context
        with configure_scope() as scope:
            if hasattr(scope, "_contexts") and "user_journey" in scope._contexts:
                scope._contexts["user_journey"]["steps"] = self.journey_steps

        add_breadcrumb(
            message=f"Journey step: {step_name}",
            category="user_journey",
            level="info",
            data=step,
        )

    def complete_journey(self, success: bool = True, final_data: Optional[Dict] = None):
        """
        Complete the current user journey.

        Args:
            success: Whether the journey completed successfully
            final_data: Final data for the journey
        """
        with configure_scope() as scope:
            if hasattr(scope, "_contexts") and "user_journey" in scope._contexts:
                scope._contexts["user_journey"].update(
                    {
                        "completed_at": datetime.utcnow().isoformat(),
                        "success": success,
                        "final_data": final_data or {},
                    }
                )

        set_tag("journey_success", success)

        add_breadcrumb(
            message=f"Journey completed: {'success' if success else 'failure'}",
            category="user_journey",
            level="info" if success else "warning",
            data={"success": success, "final_data": final_data},
        )


class SentryBusinessMetrics:
    """
    Tracks business-specific metrics and KPIs through Sentry.
    """

    @staticmethod
    def track_conversion_funnel(
        funnel_name: str,
        step: str,
        user_id: str = None,
        conversion_data: Optional[Dict] = None,
    ):
        """
        Track conversion funnel progress.

        Args:
            funnel_name: Name of the conversion funnel
            step: Current step in the funnel
            user_id: User ID for tracking
            conversion_data: Additional conversion data
        """
        set_context(
            "conversion_funnel",
            {
                "funnel_name": funnel_name,
                "step": step,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "data": conversion_data or {},
            },
        )

        set_tag("funnel_name", funnel_name)
        set_tag("funnel_step", step)
        if user_id:
            set_tag("funnel_user_id", user_id)

    @staticmethod
    def track_feature_usage(
        feature_name: str,
        usage_type: str,
        user_id: str = None,
        usage_data: Optional[Dict] = None,
    ):
        """
        Track feature usage for product analytics.

        Args:
            feature_name: Name of the feature
            usage_type: Type of usage (view, click, complete, etc.)
            user_id: User ID for tracking
            usage_data: Additional usage data
        """
        set_context(
            "feature_usage",
            {
                "feature_name": feature_name,
                "usage_type": usage_type,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "data": usage_data or {},
            },
        )

        set_tag("feature_name", feature_name)
        set_tag("usage_type", usage_type)
        if user_id:
            set_tag("feature_user_id", user_id)

    @staticmethod
    def track_performance_kpi(
        kpi_name: str,
        value: float,
        unit: str = None,
        target: float = None,
        user_context: Optional[Dict] = None,
    ):
        """
        Track performance KPIs and metrics.

        Args:
            kpi_name: Name of the KPI (response_time, conversion_rate, etc.)
            value: Measured value
            unit: Unit of measurement (ms, %, etc.)
            target: Target value for comparison
            user_context: User context data
        """
        kpi_data = {
            "kpi_name": kpi_name,
            "value": value,
            "unit": unit,
            "target": target,
            "timestamp": datetime.utcnow().isoformat(),
            "user_context": user_context or {},
        }

        set_context("performance_kpi", kpi_data)
        set_tag("kpi_name", kpi_name)
        set_tag("kpi_value", str(value))

        # Check if value exceeds target (for alerting)
        if target and value > target:
            set_tag("kpi_exceeds_target", True)


class SentryAlertManager:
    """
    Manages custom alerting and notification logic.
    """

    @staticmethod
    def trigger_business_alert(
        alert_type: str, severity: str, message: str, context: Optional[Dict] = None
    ):
        """
        Trigger business-specific alerts.

        Args:
            alert_type: Type of alert (high_error_rate, user_drop_off, etc.)
            severity: Severity level (low, medium, high, critical)
            message: Alert message
            context: Additional context data
        """
        set_context(
            "business_alert",
            {
                "alert_type": alert_type,
                "severity": severity,
                "message": message,
                "context": context or {},
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        set_tag("alert_type", alert_type)
        set_tag("alert_severity", severity)

        # Determine Sentry level based on severity
        level_mapping = {
            "low": "info",
            "medium": "warning",
            "high": "error",
            "critical": "fatal",
        }

        sentry_level = level_mapping.get(severity, "warning")

        sentry_sdk.capture_message(
            f"Business Alert: {alert_type} - {message}", level=sentry_level
        )


# Singleton instances for global use
release_tracker = SentryReleaseTracker()
error_grouping = SentryErrorGrouping()
user_journey = SentryUserJourney()
business_metrics = SentryBusinessMetrics()
alert_manager = SentryAlertManager()
