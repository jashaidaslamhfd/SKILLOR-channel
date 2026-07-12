import logging
import re
from typing import Dict, List
from collections import Counter
import hashlib

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AntiSpamSystem:
    """
    Comprehensive anti-spam system to prevent YouTube spam flags.
    Goal: Reduce swap rate from 72% to 20%
    """
    
    def __init__(self):
        self.min_hours_between_posts = 2
        self.keyword_frequency_threshold = 0.15  # 15% max
        self.similarity_threshold = 0.7  # 70% similarity = potential spam
    
    def check_for_spam_risks(self, video: Dict, previous_videos: List[Dict]) -> Dict:
        """
        Comprehensive spam risk check.
        """
        risks = []
        scores = {}
        
        # 1. Check keyword stuffing
        keyword_score = self._check_keyword_stuffing(video)
        scores['keyword_stuffing_score'] = keyword_score
        if keyword_score > 70:
            risks.append(f"🚨 CRITICAL: Keyword stuffing detected ({keyword_score}/100)")
        elif keyword_score > 50:
            risks.append(f"⚠️ WARNING: Possible keyword stuffing ({keyword_score}/100)")
        
        # 2. Check similarity to previous videos
        similarity_issues = self._check_content_similarity(video, previous_videos)
        scores['similarity_issues'] = len(similarity_issues)
        risks.extend(similarity_issues)
        
        # 3. Check for duplicate metadata
        duplicate_issues = self._check_duplicates(video, previous_videos)
        scores['duplicate_issues'] = len(duplicate_issues)
        risks.extend(duplicate_issues)
        
        # 4. Check title quality
        title_issues = self._check_title_quality(video.get('title', ''))
        scores['title_quality_issues'] = len(title_issues)
        risks.extend(title_issues)
        
        # 5. Check for engagement bait
        engagement_bait_score = self._check_engagement_bait(video)
        scores['engagement_bait_score'] = engagement_bait_score
        if engagement_bait_score > 60:
            risks.append(f"⚠️ WARNING: Possible engagement bait ({engagement_bait_score}/100)")
        
        # Overall spam risk
        spam_risk = self._calculate_overall_spam_risk(scores)
        
        return {
            'spam_risk_level': spam_risk,
            'risks': risks,
            'scores': scores,
            'recommendation': self._get_spam_recommendation(spam_risk, risks)
        }
    
    def _check_keyword_stuffing(self, video: Dict) -> float:
        """
        Detect keyword stuffing (0-100, where 100 is worst).
        """
        text = (video.get('title', '') + ' ' + video.get('voiceover', '')).lower()
        words = text.split()
        
        if not words:
            return 0
        
        # Count word frequencies
        word_counts = Counter(words)
        
        # Check for repeated keywords
        stuffing_score = 0
        for word, count in word_counts.items():
            if len(word) > 4:  # Only check meaningful words
                frequency = count / len(words)
                if frequency > self.keyword_frequency_threshold:
                    # Penalize based on how much over threshold
                    over_threshold = frequency - self.keyword_frequency_threshold
                    stuffing_score += over_threshold * 100
        
        return min(stuffing_score, 100)
    
    def _check_content_similarity(self, video: Dict, previous_videos: List[Dict]) -> List[str]:
        """
        Check if video is too similar to previous uploads.
        """
        issues = []
        
        if not previous_videos:
            return issues
        
        current_hash = self._get_content_hash(video)
        
        for prev_video in previous_videos[-10:]:  # Check last 10 videos
            prev_hash = self._get_content_hash(prev_video)
            
            if current_hash == prev_hash:
                issues.append(
                    f"🚨 CRITICAL: Content is an exact duplicate of a recent video "
                    f"'{prev_video.get('title', 'Unknown')[:30]}...'"
                )
                continue
            
            similarity = self._calculate_similarity(video, prev_video)
            
            if similarity > 0.85:
                issues.append(
                    f"🚨 CRITICAL: Content 85%+ similar to recent video "
                    f"'{prev_video.get('title', 'Unknown')[:30]}...'"
                )
            elif similarity > 0.7:
                issues.append(
                    f"⚠️ WARNING: Content {similarity:.0%} similar to recent video. "
                    f"Consider adding unique angles."
                )
        
        return issues
    
    def _check_duplicates(self, video: Dict, previous_videos: List[Dict]) -> List[str]:
        """
        Check for duplicate titles or descriptions.
        """
        issues = []
        
        current_title = video.get('title', '').lower().strip()
        current_desc = video.get('voiceover', '')[:100].lower().strip()
        
        for prev_video in previous_videos[-5:]:
            prev_title = prev_video.get('title', '').lower().strip()
            prev_desc = prev_video.get('voiceover', '')[:100].lower().strip()
            
            if current_title == prev_title:
                issues.append(
                    f"🚨 CRITICAL: Duplicate title found: '{current_title}'"
                )
            elif current_desc and current_desc == prev_desc:
                issues.append(
                    f"🚨 CRITICAL: Duplicate description/opening found (matches "
                    f"'{prev_video.get('title', 'Unknown')[:30]}...')"
                )
            elif self._are_titles_similar(current_title, prev_title):
                issues.append(
                    f"⚠️ WARNING: Very similar title to: '{prev_title}'"
                )
        
        return issues
    
    def _check_title_quality(self, title: str) -> List[str]:
        """
        Check if title has spam characteristics.
        """
        issues = []
        
        if not title:
            issues.append("❌ Empty title")
            return issues
        
        # Check for ALL CAPS
        if title.isupper():
            issues.append("⚠️ Title is ALL CAPS (can trigger spam)")
        
        # Check for too many punctuation
        punct_count = sum(1 for c in title if c in '!?.')
        if punct_count > 2:
            issues.append(f"⚠️ Too many punctuation marks ({punct_count}) - can seem spammy")
        
        # Check for excessive numbers
        numbers = re.findall(r'\d+', title)
        if len(numbers) > 3:
            issues.append("⚠️ Too many numbers - can seem spammy")
        
        # Check title length
        if len(title) < 5:
            issues.append("❌ Title too short (min 5 characters)")
        elif len(title) > 100:
            issues.append("⚠️ Title too long (YouTube recommends <60 chars)")
        
        return issues
    
    def _check_engagement_bait(self, video: Dict) -> float:
        """
        Detect engagement bait (0-100, where 100 is worst).
        """
        text = (video.get('title', '') + ' ' + video.get('voiceover', '')).lower()
        
        bait_score = 0
        
        # Phrases that encourage artificial engagement
        bait_phrases = {
            'like if': 5,
            'comment if': 5,
            'tag someone': 5,
            'share this': 3,
            'smash like': 8,
            'hit like': 8,
            'double tap': 5,
            'subscribe for': 2,  # Normal but watch for abuse
            'don\'t forget': 3,
        }
        
        for phrase, weight in bait_phrases.items():
            if phrase in text:
                bait_score += weight
        
        return min(bait_score, 100)
    
    def _calculate_overall_spam_risk(self, scores: Dict) -> str:
        """
        Calculate overall spam risk level.
        """
        keyword_score = scores.get('keyword_stuffing_score', 0)
        bait_score = scores.get('engagement_bait_score', 0)
        similarity = scores.get('similarity_issues', 0)
        duplicates = scores.get('duplicate_issues', 0)
        
        # Weight the scores
        weighted_risk = (keyword_score * 0.4) + (bait_score * 0.3) + \
                       (similarity * 20) + (duplicates * 30)
        
        if weighted_risk > 60 or duplicates > 0:
            return 'CRITICAL'
        elif weighted_risk > 40 or similarity > 1:
            return 'HIGH'
        elif weighted_risk > 20:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _get_spam_recommendation(self, risk_level: str, risks: List[str]) -> str:
        """
        Get recommendation based on spam risk.
        """
        if risk_level == 'CRITICAL':
            return "🔴 DO NOT PUBLISH - High spam risk. Rewrite content significantly."
        elif risk_level == 'HIGH':
            return "🟠 CAUTION - Address issues before publishing"
        elif risk_level == 'MEDIUM':
            return "🟡 REVIEW - Minor issues detected, consider improvements"
        else:
            return "🟢 SAFE - Low spam risk. Can publish."
    
    def _calculate_similarity(self, video1: Dict, video2: Dict) -> float:
        """
        Calculate overall content similarity (0-1).
        """
        title1 = video1.get('title', '').lower()
        title2 = video2.get('title', '').lower()
        desc1 = video1.get('voiceover', '')[:200].lower()
        desc2 = video2.get('voiceover', '')[:200].lower()
        
        # Title similarity weight: 0.3
        title_similarity = self._string_similarity(title1, title2) * 0.3
        
        # Description similarity weight: 0.7
        desc_similarity = self._string_similarity(desc1, desc2) * 0.7
        
        return title_similarity + desc_similarity
    
    def _string_similarity(self, s1: str, s2: str) -> float:
        """
        Calculate string similarity using word overlap.
        """
        words1 = set(s1.split())
        words2 = set(s2.split())
        
        if not words1 or not words2:
            return 0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0
    
    def _are_titles_similar(self, title1: str, title2: str) -> bool:
        """
        Check if titles are too similar.
        """
        # Simple check: same words in different order
        words1 = set(title1.split())
        words2 = set(title2.split())
        
        if not words1 or not words2:
            return False
        
        # If 70%+ words are same, titles are similar
        common = len(words1.intersection(words2))
        total = len(words1.union(words2))
        
        return common / total > 0.7
    
    def _get_content_hash(self, video: Dict) -> str:
        """
        Get hash of video content for quick comparison.
        """
        content = (video.get('title', '') + video.get('voiceover', '')).lower()
        return hashlib.md5(content.encode()).hexdigest()
    
    def generate_anti_spam_report(self, video: Dict, previous_videos: List[Dict]) -> str:
        """
        Generate detailed anti-spam report.
        """
        result = self.check_for_spam_risks(video, previous_videos)
        
        report = "\n🛡️ ANTI-SPAM ANALYSIS REPORT\n"
        report += "=" * 50 + "\n"
        report += f"\nSpam Risk Level: {result['spam_risk_level']}\n"
        report += f"Recommendation: {result['recommendation']}\n"
        report += "\nDetailed Scores:\n"
        
        for key, score in result['scores'].items():
            report += f"  • {key}: {score}\n"
        
        if result['risks']:
            report += "\nIssues Found:\n"
            for risk in result['risks']:
                report += f"  {risk}\n"
        else:
            report += "\n✅ No spam issues detected.\n"
        
        return report


if __name__ == "__main__":
    system = AntiSpamSystem()
    
    test_video = {
        'title': 'Why Babies Need Crawling: The Brain Science Explained',
        'voiceover': '''Babies who crawl develop better brains. Scientists found that 
        crawling helps brain development significantly. Your baby needs crawling. 
        Make sure your baby crawls for better development.'''
    }
    
    result = system.check_for_spam_risks(test_video, [])
    print(system.generate_anti_spam_report(test_video, []))
