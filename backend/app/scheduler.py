"""
Scheduled reporting service for Airflow Health Dashboard.

This module handles scheduled health reports sent via Slack at configured times
(default: 10 AM and 7 PM daily).
"""

import asyncio
import logging
from datetime import datetime, time
from typing import Optional
from .service import health_service
from .slack_service import slack_service
from .models import TimeRange
from .llm_service import llm_service
from .config import settings

logger = logging.getLogger(__name__)


class ScheduledReporter:
    """Manages scheduled health reports."""
    
    def __init__(
        self,
        morning_time: time = time(10, 0),  # 10:00 AM
        evening_time: time = time(19, 0),  # 7:00 PM
        dashboard_url: str = "https://dashboard.yourcompany.com"
    ):
        """
        Initialize scheduled reporter.
        
        Args:
            morning_time: Time for morning report (default: 10:00 AM)
            evening_time: Time for evening report (default: 7:00 PM)
            dashboard_url: URL to the dashboard
        """
        self.morning_time = morning_time
        self.evening_time = evening_time
        self.dashboard_url = dashboard_url
        self.running = False
    
    async def generate_and_send_report(
        self,
        time_range: TimeRange = TimeRange.HOURS_24,
        include_ai_analysis: bool = True
    ) -> bool:
        """
        Generate health report and send to Slack.
        
        Args:
            time_range: Time range for the report
            include_ai_analysis: Whether to include AI failure analysis
            
        Returns:
            bool: True if report sent successfully
        """
        try:
            logger.info(f"Generating scheduled report for time range: {time_range.value}")
            
            # Get dashboard data
            dashboard_data = await health_service.get_dashboard_data(time_range)
            
            if not dashboard_data or not dashboard_data.domains:
                logger.warning("No domain data available for report")
                return False
            
            # Get AI analysis if enabled and there are failures
            ai_analysis = None
            total_failures = sum(d.failed_count for d in dashboard_data.domains)
            
            if include_ai_analysis and total_failures > 0:
                try:
                    logger.info("Generating AI failure analysis for report")
                    # Analyze failures across all domains
                    ai_analysis = await llm_service.analyze_domain_failures(
                        dashboard_data.domains,
                        time_range
                    )
                except Exception as e:
                    logger.error(f"AI analysis failed, continuing without it: {str(e)}")
            
            # Send Slack notification
            success = await slack_service.send_health_summary(
                domains=dashboard_data.domains,
                time_range=time_range,
                dashboard_url=self.dashboard_url,
                ai_analysis=ai_analysis
            )
            
            if success:
                logger.info(f"Scheduled report sent successfully at {datetime.now()}")
            else:
                logger.error("Failed to send scheduled report")
            
            return success
            
        except Exception as e:
            logger.error(f"Error generating scheduled report: {str(e)}")
            return False
    
    async def run_scheduler(self):
        """
        Run the scheduler loop.
        This checks every minute if it's time to send a report.
        """
        self.running = True
        logger.info(
            f"Scheduler started. Reports will be sent at "
            f"{self.morning_time.strftime('%H:%M')} and "
            f"{self.evening_time.strftime('%H:%M')}"
        )
        
        last_morning_date = None
        last_evening_date = None
        
        while self.running:
            try:
                now = datetime.now()
                current_time = now.time()
                current_date = now.date()
                
                # Check if it's time for morning report
                if (
                    self._is_time_to_report(current_time, self.morning_time) and
                    current_date != last_morning_date
                ):
                    logger.info("Triggering morning report")
                    await self.generate_and_send_report(
                        time_range=TimeRange.HOURS_24,
                        include_ai_analysis=True
                    )
                    last_morning_date = current_date
                
                # Check if it's time for evening report
                elif (
                    self._is_time_to_report(current_time, self.evening_time) and
                    current_date != last_evening_date
                ):
                    logger.info("Triggering evening report")
                    await self.generate_and_send_report(
                        time_range=TimeRange.HOURS_24,
                        include_ai_analysis=True
                    )
                    last_evening_date = current_date
                
                # Wait 60 seconds before checking again
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {str(e)}")
                await asyncio.sleep(60)  # Continue after error
    
    def _is_time_to_report(self, current_time: time, target_time: time) -> bool:
        """
        Check if current time matches target time (within 1 minute window).
        
        Args:
            current_time: Current time
            target_time: Target report time
            
        Returns:
            bool: True if within reporting window
        """
        # Check if we're within 1 minute of target time
        current_minutes = current_time.hour * 60 + current_time.minute
        target_minutes = target_time.hour * 60 + target_time.minute
        
        # Allow 1-minute window
        return abs(current_minutes - target_minutes) <= 1
    
    def stop(self):
        """Stop the scheduler."""
        logger.info("Stopping scheduler")
        self.running = False


# For AWS EventBridge Lambda integration
async def lambda_handler(event: dict, context: Optional[dict] = None) -> dict:
    """
    AWS Lambda handler for EventBridge scheduled events.
    
    This function is triggered by EventBridge at scheduled times (10 AM and 7 PM).
    
    Args:
        event: EventBridge event data
        context: Lambda context (optional)
        
    Returns:
        dict: Response with status code and message
    """
    try:
        logger.info(f"Lambda handler triggered by EventBridge: {event}")
        
        # Determine which report to send based on event detail
        report_type = event.get('detail-type', 'scheduled-report')
        
        # Create reporter instance
        reporter = ScheduledReporter()
        
        # Generate and send report
        success = await reporter.generate_and_send_report(
            time_range=TimeRange.HOURS_24,
            include_ai_analysis=True
        )
        
        if success:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': f'Report sent successfully at {datetime.now().isoformat()}',
                    'report_type': report_type
                })
            }
        else:
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'message': 'Failed to send report',
                    'report_type': report_type
                })
            }
    
    except Exception as e:
        logger.error(f"Lambda handler error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }


# For standalone execution (testing)
async def main():
    """Main function for testing scheduled reports."""
    import sys
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    reporter = ScheduledReporter()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--schedule':
        # Run scheduler
        logger.info("Starting scheduler mode")
        await reporter.run_scheduler()
    else:
        # Send immediate test report
        logger.info("Sending test report")
        success = await reporter.generate_and_send_report()
        if success:
            print("✅ Test report sent successfully!")
        else:
            print("❌ Failed to send test report")
            sys.exit(1)


if __name__ == "__main__":
    import json
    asyncio.run(main())


# Global instance for integration with FastAPI
scheduled_reporter = ScheduledReporter()
