from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from jobs.models import JobCategory, Skill, Company, JobPosting, JobSkill
from .engine import (
    predict_salary, job_match_score, recommend_jobs_for_profile, trending_skills,
    skill_gap_analysis, market_position_for_profile,
)
from .models import SalaryTrendSnapshot, PredictionQuery


class SalaryPredictionEngineTests(TestCase):
    def setUp(self):
        self.category = JobCategory.objects.create(name='Software Engineering')

    def test_predict_salary_returns_sane_range(self):
        result = predict_salary(category=self.category, location='Austin, TX', experience_level='mid')
        self.assertGreater(result.predicted_max, result.predicted_min)
        self.assertGreater(result.predicted_min, 0)
        self.assertTrue(0 <= result.confidence <= 100)

    def test_higher_experience_yields_higher_salary(self):
        entry = predict_salary(category=self.category, location='Austin, TX', experience_level='entry')
        senior = predict_salary(category=self.category, location='Austin, TX', experience_level='senior')
        self.assertGreater(senior.predicted_mid, entry.predicted_mid)

    def test_location_multiplier_affects_salary(self):
        sf = predict_salary(category=self.category, location='San Francisco, CA', experience_level='mid')
        remote_low_col = predict_salary(category=self.category, location='Bangalore, India', experience_level='mid')
        self.assertGreater(sf.predicted_mid, remote_low_col.predicted_mid)

    def test_skills_add_premium(self):
        skill = Skill.objects.create(name='Machine Learning', skill_type='technical')
        without_skills = predict_salary(category=self.category, location='Austin, TX', experience_level='mid')
        with_skills = predict_salary(
            category=self.category, location='Austin, TX', experience_level='mid', skills=[skill]
        )
        self.assertGreaterEqual(with_skills.predicted_mid, without_skills.predicted_mid)

    def test_market_data_blends_in_and_raises_confidence(self):
        for i in range(3):
            SalaryTrendSnapshot.objects.create(
                category=self.category, location='Austin, TX', period=f'2024-0{i+1}-01',
                avg_salary=150000, min_salary=130000, max_salary=170000, job_count=10,
            )
        result = predict_salary(category=self.category, location='Austin, TX', experience_level='mid')
        self.assertGreaterEqual(result.confidence, 55)
        self.assertIn('blended', result.basis)


class JobMatchScoreTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='matcher', password='testpass123')
        self.category = JobCategory.objects.create(name='Software Engineering')
        self.company = Company.objects.create(name='MatchCo')
        self.python = Skill.objects.create(name='Python')
        self.sql = Skill.objects.create(name='SQL')
        self.job = JobPosting.objects.create(
            title='Backend Engineer', company=self.company, category=self.category,
            description='...', location='Remote', remote_option='remote',
            experience_level='mid', salary_min=90000, salary_max=120000,
        )
        JobSkill.objects.create(job=self.job, skill=self.python, importance='required')
        JobSkill.objects.create(job=self.job, skill=self.sql, importance='preferred')

    def test_score_increases_with_matching_skills(self):
        profile = self.user.profile
        result_no_skills = job_match_score(profile, self.job)
        profile.skills.add(self.python)
        result_with_skill = job_match_score(profile, self.job)
        self.assertGreater(result_with_skill['score'], result_no_skills['score'])

    def test_remote_preference_boosts_score(self):
        profile = self.user.profile
        profile.open_to_remote = True
        profile.save()
        result = job_match_score(profile, self.job)
        self.assertGreater(result['score'], 0)

    def test_recommend_jobs_for_profile_returns_scored_jobs(self):
        profile = self.user.profile
        profile.skills.add(self.python, self.sql)
        profile.save()
        scored = recommend_jobs_for_profile(profile, limit=5)
        self.assertTrue(len(scored) >= 1)
        job, result = scored[0]
        self.assertIn('score', result)
        self.assertIn('reasons', result)


class TrendingSkillsTests(TestCase):
    def test_trending_skills_ranks_by_demand(self):
        category = JobCategory.objects.create(name='Data Science & Analytics')
        company = Company.objects.create(name='TrendCo')
        popular = Skill.objects.create(name='SQL')
        rare = Skill.objects.create(name='COBOL')
        for i in range(3):
            job = JobPosting.objects.create(
                title=f'Data Role {i}', company=company, category=category,
                description='...', location='Remote',
            )
            JobSkill.objects.create(job=job, skill=popular, importance='required')
        job = JobPosting.objects.create(
            title='Legacy Role', company=company, category=category, description='...', location='Remote',
        )
        JobSkill.objects.create(job=job, skill=rare, importance='required')

        top = list(trending_skills(limit=5))
        self.assertEqual(top[0], popular)


class AnalyticsViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = JobCategory.objects.create(name='Product Management')
        self.company = Company.objects.create(name='ProductCo')
        JobPosting.objects.create(
            title='Product Manager', company=self.company, category=self.category,
            description='...', location='Remote', salary_min=100000, salary_max=140000,
        )

    def test_dashboard_loads(self):
        response = self.client.get(reverse('analytics:dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_salary_predictor_get(self):
        response = self.client.get(reverse('analytics:salary_predictor'))
        self.assertEqual(response.status_code, 200)

    def test_salary_predictor_post_logs_query(self):
        response = self.client.post(reverse('analytics:salary_predictor'), {
            'category': self.category.id, 'location': 'Remote', 'experience_level': 'mid',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(PredictionQuery.objects.count(), 1)

    def test_recommendations_requires_login(self):
        response = self.client.get(reverse('analytics:recommendations'))
        self.assertEqual(response.status_code, 302)

    def test_predict_salary_api(self):
        response = self.client.post('/api/predict-salary/', {
            'location': 'Austin, TX', 'experience_level': 'senior',
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('predicted_min', data)
        self.assertIn('predicted_max', data)


class SkillGapAnalysisTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='gapuser', password='testpass123')
        self.category = JobCategory.objects.create(name='Software Engineering')
        self.company = Company.objects.create(name='GapCo')
        self.python = Skill.objects.create(name='Python')
        self.kubernetes = Skill.objects.create(name='Kubernetes')

        for i in range(3):
            job = JobPosting.objects.create(
                title='Backend Engineer', company=self.company, category=self.category,
                description='...', location='Remote', is_active=True,
            )
            JobSkill.objects.create(job=job, skill=self.python, importance='required')
            JobSkill.objects.create(job=job, skill=self.kubernetes, importance='required')

    def test_missing_skill_is_flagged(self):
        profile = self.user.profile
        profile.desired_role = 'Backend Engineer'
        profile.skills.add(self.python)
        profile.save()

        result = skill_gap_analysis(profile)
        have_names = [e['skill'].name for e in result['have']]
        missing_names = [e['skill'].name for e in result['missing']]
        self.assertIn('Python', have_names)
        self.assertIn('Kubernetes', missing_names)
        self.assertTrue(result['role_specific'])

    def test_falls_back_to_all_jobs_without_matching_role(self):
        profile = self.user.profile
        profile.desired_role = 'Nonexistent Role XYZ'
        profile.save()
        result = skill_gap_analysis(profile)
        self.assertFalse(result['role_specific'])
        self.assertGreater(result['role_matched_jobs'], 0)


class MarketPositionTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='posuser', password='testpass123')
        self.python = Skill.objects.create(name='Python')

    def test_market_position_computes_gap(self):
        profile = self.user.profile
        profile.desired_location = 'Austin, TX'
        profile.experience_level = 'mid'
        profile.expected_salary = 500000  # unrealistically high
        profile.save()
        profile.skills.add(self.python)

        result = market_position_for_profile(profile)
        self.assertIsNotNone(result['gap'])
        self.assertGreater(result['gap'], 0)  # expectation far above market estimate

    def test_market_position_view_requires_login(self):
        response = self.client.get(reverse('analytics:market_position'))
        self.assertEqual(response.status_code, 302)

    def test_market_position_view_loads_for_logged_in_user(self):
        self.client.login(username='posuser', password='testpass123')
        response = self.client.get(reverse('analytics:market_position'))
        self.assertEqual(response.status_code, 200)
