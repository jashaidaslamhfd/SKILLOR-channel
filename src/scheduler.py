import logging
from datetime import datetime, timedelta
from typing import List, Dict
import pytz

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class FrancePeakTimeScheduler:
    """
    Intelligent scheduler for posting at France/Europe peak times.
    Tuned for adult francophone short-form education/wellness audience behavior.
    """

    # France peak times for short-form engagement (Europe/Paris)
    PEAK_TIMES = [
        {'hour': 7, 'minute': 30, 'zone': 'FR', 'name': 'Trajet du matin'},
        {'hour': 12, 'minute': 15, 'zone': 'FR', 'name': 'Pause déjeuner'},
        {'hour': 20, 'minute': 30, 'zone': 'FR', 'name': 'Soirée'},
    ]

    # Key francophone timezones
    TIMEZONE_MAP = {
        'FR': 'Europe/Paris',
        'BE': 'Europe/Brussels',
        'CH': 'Europe/Zurich',
        'CA_FR': 'America/Toronto',
    }

    def __init__(self):
        self.fr_tz = pytz.timezone(self.TIMEZONE_MAP['FR'])
        self.utc_tz = pytz.UTC

    def get_next_posting_times(self, num_posts: int = 3) -> List[Dict]:
        """
        Get next optimal posting times for videos.

        Args:
            num_posts: Number of daily posts.

        Returns:
            List of optimal posting times with timezone info.
        """
        posting_schedule = []

        for i in range(num_posts):
            if i < len(self.PEAK_TIMES):
                peak_time = self.PEAK_TIMES[i]
                next_post_time = self._get_next_occurrence(
                    peak_time['hour'],
                    peak_time['minute']
                )

                posting_schedule.append({
                    'time': next_post_time,
                    'time_fr': next_post_time.strftime('%Y-%m-%d %H:%M:%S France'),
                    'time_utc': next_post_time.astimezone(self.utc_tz).strftime('%Y-%m-%d %H:%M:%S UTC'),
                    'peak_name': peak_time['name'],
                    'reason': self._get_posting_reason(peak_time['name'])
                })

        return posting_schedule

    def _get_next_occurrence(self, hour: int, minute: int) -> datetime:
        """Get next occurrence of a specific time in France."""
        now = datetime.now(self.fr_tz)
        next_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # If time has passed today, schedule for tomorrow
        if next_time <= now:
            next_time += timedelta(days=1)

        return next_time

    def _get_posting_reason(self, peak_name: str) -> str:
        """Get reason why this is a peak time for this content."""
        reasons = {
            'Trajet du matin': 'Scroll dans les transports / café du matin',
            'Pause déjeuner': 'Pause rapide avec forte intention de regarder des Shorts éducatifs',
            'Soirée': 'Scroll du soir avant sommeil, forte affinité avec cerveau/sommeil/stress',
        }
        return reasons.get(peak_name, 'Heure de forte activité francophone')

    def get_publishing_metadata(self, posting_time: datetime) -> Dict:
        """Get YouTube API compatible publishing metadata."""
        utc_time = posting_time.astimezone(self.utc_tz)

        return {
            'publishAt': utc_time.isoformat(),
            'privacyStatus': 'public',
            'releaseTime': utc_time.isoformat(),
            'timezone': 'Europe/Paris',
            'localTime': posting_time.strftime('%Y-%m-%d %H:%M:%S'),
        }

    def validate_posting_interval(self, last_post_time: datetime) -> bool:
        """
        Validate minimum 2-hour interval between posts to avoid spam flagging.

        Accepts either a naive or timezone-aware datetime.
        Naive datetimes are assumed to already be UTC, matching how
        video_history.json stores them.
        """
        if last_post_time.tzinfo is None:
            last_post_time = last_post_time.replace(tzinfo=pytz.UTC)

        now = datetime.now(self.fr_tz)
        time_since_last = (now - last_post_time).total_seconds() / 3600

        if time_since_last < 2:
            logger.warning(f"⚠️ Only {time_since_last:.1f} hours since last post")
            return False

        return True

    def get_daily_schedule(self) -> str:
        """Get formatted daily schedule."""
        schedule = self.get_next_posting_times(3)

        formatted = "📅 Daily Posting Schedule (France)\n"
        formatted += "=" * 50 + "\n"

        for i, post in enumerate(schedule, 1):
            formatted += f"\nPost {i}: {post['time_fr']}\n"
            formatted += f"  Peak: {post['peak_name']}\n"
            formatted += f"  Reason: {post['reason']}\n"
            formatted += f"  UTC: {post['time_utc']}\n"

        return formatted

    def get_timezone_conversion(self, france_time: datetime) -> Dict[str, str]:
        """Convert France time to key francophone timezones."""
        conversions = {}

        for zone_name, zone_path in self.TIMEZONE_MAP.items():
            tz = pytz.timezone(zone_path)
            converted = france_time.astimezone(tz)
            conversions[zone_name] = converted.strftime('%H:%M:%S')

        return conversions

    def suggest_optimal_schedule(self) -> List[Dict]:
        """
        Suggest optimal posting schedule based on adult French audience patterns.

        Recommended daily windows:
        - Morning commute / coffee
        - Lunch break
        - Evening / before sleep
        """
        recommendations = [
            {
                'slot': 1,
                'time': '07:30 Europe/Paris',
                'audience': 'Trajet du matin / café',
                'expected_engagement': 'High',
                'reason': 'Bon moment pour un fait court cerveau/sommeil avant le travail'
            },
            {
                'slot': 2,
                'time': '12:15 Europe/Paris',
                'audience': 'Pause déjeuner',
                'expected_engagement': 'Very High',
                'reason': 'Fenêtre courte parfaite pour micro-learning et partage'
            },
            {
                'slot': 3,
                'time': '20:30 Europe/Paris',
                'audience': 'Soirée / avant sommeil',
                'expected_engagement': 'High',
                'reason': 'Très adapté aux sujets sommeil, stress et cerveau'
            }
        ]

        return recommendations


if __name__ == "__main__":
    scheduler = FrancePeakTimeScheduler()

    print(scheduler.get_daily_schedule())
    print("\n" + "=" * 50)
    print("\n📊 Optimal Schedule Recommendations:\n")

    for rec in scheduler.suggest_optimal_schedule():
        print(f"Slot {rec['slot']}: {rec['time']}")
        print(f"  Audience: {rec['audience']}")
        print(f"  Expected Engagement: {rec['expected_engagement']}")
        print(f"  Reason: {rec['reason']}\n")


# Backward compatibility for older imports in main.py
USAPeakTimeScheduler = FrancePeakTimeScheduler
