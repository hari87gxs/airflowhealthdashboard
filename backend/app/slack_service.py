"""
Slack notification service for Airflow Health Dashboard.

This module provides functionality to send rich formatted messages to Slack
including health summaries, failure analysis, and dashboard links.
"""

import httpx
import json
from typing import Dict, List, Optional
from datetime import datetime
from .models import DomainHealthSummary, TimeRange
from .config import settings
import logging

logger = logging.getLogger(__name__)


class SlackService:
    """Service for sending formatted Slack notifications."""
    
    def __init__(self, webhook_url: Optional[str] = None):
        """
        Initialize Slack service.
        
        Args:
            webhook_url: Slack webhook URL. If not provided, uses settings.
        """
        self.webhook_url = webhook_url or settings.slack_webhook_url
        if not self.webhook_url:
            logger.warning("Slack webhook URL not configured")
    
    async def send_health_summary(
        self,
        domains: List[DomainHealthSummary],
        time_range: TimeRange,
        dashboard_url: str = "https://dashboard.yourcompany.com",
        ai_analysis: Optional[Dict] = None
    ) -> bool:
        """
        Send health summary notification to Slack.
        
        Args:
            domains: List of domain health summaries
            time_range: Time range for the report
            dashboard_url: URL to the dashboard
            ai_analysis: Optional AI analysis results
            
        Returns:
            bool: True if message sent successfully, False otherwise
        """
        if not self.webhook_url:
            logger.error("Cannot send Slack message: webhook URL not configured")
            return False
        
        # Calculate overall metrics
        total_dags = sum(d.total_dags for d in domains)
        total_failures = sum(d.failed_count for d in domains)
        total_success = sum(d.success_count for d in domains)
        overall_health = (total_success / (total_success + total_failures) * 100) if (total_success + total_failures) > 0 else 100
        
        # Sort domains: failures first
        sorted_domains = sorted(domains, key=lambda x: (-x.failed_count, x.domain_tag))
        
        # Build Slack message
        message = self._build_health_message(
            sorted_domains,
            time_range,
            total_dags,
            total_failures,
            overall_health,
            dashboard_url,
            ai_analysis
        )
        
        # Send to Slack
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.webhook_url,
                    json=message,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    logger.info(f"Slack notification sent successfully")
                    return True
                else:
                    logger.error(f"Slack notification failed: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error sending Slack notification: {str(e)}")
            return False
    
    def _build_health_message(
        self,
        domains: List[DomainHealthSummary],
        time_range: TimeRange,
        total_dags: int,
        total_failures: int,
        overall_health: float,
        dashboard_url: str,
        ai_analysis: Optional[Dict]
    ) -> Dict:
        """Build formatted Slack message using Block Kit."""
        
        # Determine overall status emoji
        status_emoji = self._get_status_emoji(overall_health, total_failures)
        
        # Build blocks
        blocks = [
            # Header
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{status_emoji} Airflow Health Dashboard Report",
                    "emoji": True
                }
            },
            # Context (timestamp and time range)
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Report Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | *Time Range:* {time_range.value}"
                    }
                ]
            },
            {"type": "divider"},
            # Overall Summary
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Total DAGs:*\n{total_dags}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Total Failures:*\n{total_failures} :x:"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Overall Health:*\n{overall_health:.1f}%"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Domains Monitored:*\n{len(domains)}"
                    }
                ]
            }
        ]
        
        # Add domain details
        if domains:
            blocks.append({"type": "divider"})
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Domain Health Status:*"
                }
            })
            
            # Top domains (show up to 8)
            for domain in domains[:8]:
                emoji = self._get_domain_emoji(domain)
                health_bar = self._get_health_bar(domain.health_score)
                
                domain_text = (
                    f"{emoji} *{domain.domain_tag}*\n"
                    f"DAGs: {domain.total_dags} | "
                    f"Success: {domain.success_count} :white_check_mark: | "
                    f"Failed: {domain.failed_count} :x: | "
                    f"Running: {domain.running_count} :hourglass:\n"
                    f"Health: {health_bar} {domain.health_score:.1f}%"
                )
                
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": domain_text
                    }
                })
        
        # Add AI Analysis if available
        if ai_analysis and "categorized_failures" in ai_analysis:
            blocks.append({"type": "divider"})
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": ":robot_face: *AI-Powered Failure Analysis:*"
                }
            })
            
            for category, details in list(ai_analysis["categorized_failures"].items())[:3]:
                category_text = (
                    f"*{category}* ({details['count']} failures)\n"
                    f"• Severity: {details['severity']}\n"
                )
                
                if details.get('immediate_actions'):
                    category_text += f"• Action: {details['immediate_actions'][0]}\n"
                
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": category_text
                    }
                })
        
        # Add action buttons
        blocks.append({"type": "divider"})
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": ":bar_chart: View Dashboard",
                        "emoji": True
                    },
                    "url": dashboard_url,
                    "style": "primary"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": ":mag: Detailed Analysis",
                        "emoji": True
                    },
                    "url": f"{dashboard_url}/analysis"
                }
            ]
        })
        
        # Footer
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "_Automated report from Airflow Health Dashboard | Monitoring 294 DAGs across 8 domains_"
                }
            ]
        })
        
        return {"blocks": blocks}
    
    def _get_status_emoji(self, health: float, failures: int) -> str:
        """Get emoji for overall status."""
        if failures == 0:
            return ":white_check_mark:"
        elif health >= 95:
            return ":large_green_circle:"
        elif health >= 90:
            return ":large_yellow_circle:"
        elif health >= 80:
            return ":large_orange_circle:"
        else:
            return ":red_circle:"
    
    def _get_domain_emoji(self, domain: DomainHealthSummary) -> str:
        """Get emoji for domain status."""
        if domain.failed_count > 0:
            return ":red_circle:"
        elif domain.running_count > 0:
            return ":large_blue_circle:"
        else:
            return ":white_check_mark:"
    
    def _get_health_bar(self, health_score: float) -> str:
        """Generate visual health bar."""
        filled = int(health_score / 10)
        empty = 10 - filled
        return "▓" * filled + "░" * empty
    
    async def send_critical_alert(
        self,
        domain: str,
        failures: int,
        dashboard_url: str
    ) -> bool:
        """
        Send critical failure alert.
        
        Args:
            domain: Domain name with critical failures
            failures: Number of failures
            dashboard_url: URL to dashboard
            
        Returns:
            bool: True if sent successfully
        """
        if not self.webhook_url:
            return False
        
        message = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": ":rotating_light: Critical Alert: High Failure Rate",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            f":red_circle: *{domain}* domain has *{failures} failures*\n\n"
                            f"Immediate attention required!"
                        )
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "View Details",
                                "emoji": True
                            },
                            "url": f"{dashboard_url}/domain/{domain}",
                            "style": "danger"
                        }
                    ]
                }
            ]
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.webhook_url,
                    json=message,
                    headers={"Content-Type": "application/json"}
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Error sending critical alert: {str(e)}")
            return False
    
    async def test_connection(self) -> bool:
        """
        Test Slack webhook connection.
        
        Returns:
            bool: True if webhook is accessible
        """
        if not self.webhook_url:
            return False
        
        test_message = {
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": ":white_check_mark: Slack integration test successful!\n\nAirflow Health Dashboard is connected and ready to send notifications."
                    }
                }
            ]
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.webhook_url,
                    json=test_message,
                    headers={"Content-Type": "application/json"}
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Slack connection test failed: {str(e)}")
            return False


# Global instance
slack_service = SlackService()
