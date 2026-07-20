"""Tests offline de la configuration éditoriale France-first."""
import json, os, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'src'))
from seo_generator import generate_seo_package
from trend_fetcher import get_body_glitch_topics, _is_relevant
from shorts_enhancer import score_hook
class FranceChannelTests(unittest.TestCase):
    def test_catalogue_is_french_and_complete(self):
        records=get_body_glitch_topics()
        self.assertEqual(len(records),500)
        self.assertEqual(records[0]['series_title'],'Paupière qui saute')
        self.assertEqual(records[0]['source'],'body_glitch_series_fr')
        self.assertTrue(all(x['pillar']=='reflexes_du_corps' for x in records))
    def test_french_relevance_filter(self):
        self.assertTrue(_is_relevant('Pourquoi le cerveau a besoin de sommeil'))
        self.assertFalse(_is_relevant('Résultat du match de football'))
    def test_seo_is_french(self):
        package=generate_seo_package('Pourquoi une paupière tressaille',{'title':'Pourquoi la paupière tressaille','thumbnail_text':'ŒIL QUI SAUTE','hook':'Pourquoi votre paupière saute parfois','description':'Un réflexe musculaire courant peut faire tressauter une paupière.','cta':'Abonnez-vous pour plus de science simple.'})
        self.assertIn('#science',package['hashtags'])
        self.assertIn('français',package['tags'])
        # Pinned comment is now topic-specific (varied per video) instead of
        # one hardcoded string reused on every single upload - identical
        # pinned comments across a channel's uploads can look templated/spam
        # to both viewers and YouTube's systems.
        self.assertTrue(package['pinned_comment'])
        self.assertLessEqual(len(package['pinned_comment']), 200)
        self.assertEqual(package['chosen_title'], package['title'])
        self.assertEqual(package['seo_score']['scores']['overall_seo_score'],85)
        # The chosen title should be the real SEO-rich angle, not just a
        # 2-3 word branded label - this was the main bug being fixed.
        self.assertGreater(len(package['chosen_title'].split()), 3)
    def test_french_hook_receives_a_score(self):
        self.assertGreaterEqual(score_hook('Pourquoi votre cerveau remarque votre prénom')['score'],50)
if __name__=='__main__': unittest.main()
