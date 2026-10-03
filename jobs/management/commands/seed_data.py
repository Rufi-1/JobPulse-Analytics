import random
from datetime import timedelta, date

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction

from jobs.models import (
    JobCategory, Skill, Company, JobPosting, JobSkill, SavedJob, Application, JobReview,
)
from accounts.models import Profile
from analytics.models import SkillDemandSnapshot, SalaryTrendSnapshot


CATEGORIES = [
    ('Software Engineering', '💻', 'Backend, frontend, and full-stack engineering roles.'),
    ('Data Science & Analytics', '📊', 'Data science, analytics, and business intelligence roles.'),
    ('Machine Learning & AI', '🤖', 'ML engineering, applied research, and AI product roles.'),
    ('Product Management', '🧭', 'Product strategy, discovery, and delivery roles.'),
    ('Design (UX/UI)', '🎨', 'Product design, user research, and visual design roles.'),
    ('DevOps & Cloud', '☁️', 'Infrastructure, SRE, platform, and cloud engineering roles.'),
    ('Cybersecurity', '🔒', 'Security engineering, GRC, and offensive security roles.'),
    ('Sales & Business Development', '📈', 'Sales, partnerships, and revenue roles.'),
    ('Marketing', '📣', 'Growth, content, and performance marketing roles.'),
    ('Human Resources', '🧑\u200d💼', 'Talent, people ops, and HR business partner roles.'),
]

SKILLS = [
    ('Python', 'technical'), ('JavaScript', 'technical'), ('TypeScript', 'technical'),
    ('React', 'technical'), ('Vue.js', 'technical'), ('Django', 'technical'),
    ('Node.js', 'technical'), ('SQL', 'technical'), ('PostgreSQL', 'technical'),
    ('MongoDB', 'technical'), ('AWS', 'tool'), ('Google Cloud Platform', 'tool'),
    ('Azure', 'tool'), ('Docker', 'tool'), ('Kubernetes', 'tool'), ('Terraform', 'tool'),
    ('Machine Learning', 'technical'), ('Deep Learning', 'technical'), ('TensorFlow', 'tool'),
    ('PyTorch', 'tool'), ('Pandas', 'tool'), ('Data Visualization', 'technical'),
    ('Tableau', 'tool'), ('Power BI', 'tool'), ('Excel', 'tool'), ('Golang', 'technical'),
    ('Rust', 'technical'), ('Java', 'technical'), ('C++', 'technical'), ('System Design', 'technical'),
    ('REST APIs', 'technical'), ('GraphQL', 'technical'), ('CI/CD', 'technical'),
    ('Git', 'tool'), ('Agile/Scrum', 'soft'), ('Communication', 'soft'), ('Leadership', 'soft'),
    ('Problem Solving', 'soft'), ('Project Management', 'soft'), ('Figma', 'tool'),
    ('User Research', 'technical'), ('SEO', 'technical'), ('Content Strategy', 'technical'),
    ('Salesforce', 'tool'), ('Negotiation', 'soft'), ('Cybersecurity', 'technical'),
    ('Penetration Testing', 'technical'), ('Network Security', 'technical'),
    ('Cloud Architecture', 'technical'), ('Data Engineering', 'technical'),
    ('Statistics', 'technical'), ('A/B Testing', 'technical'), ('PMP', 'certification'),
    ('AWS Certified Solutions Architect', 'certification'), ('CISSP', 'certification'),
    ('Scrum Master Certification', 'certification'),
]

COMPANIES = [
    ('NimbusCloud Technologies', 'Cloud Computing', 'medium', 'San Francisco, CA', 2014),
    ('Northwind Analytics', 'Data & Analytics', 'small', 'Austin, TX', 2018),
    ('Vertex Financial Group', 'Financial Services', 'large', 'New York, NY', 1998),
    ('BrightPath Health', 'Healthcare Technology', 'medium', 'Boston, MA', 2011),
    ('Solstice Robotics', 'Robotics & Hardware', 'startup', 'Seattle, WA', 2021),
    ('Cobalt Retail Systems', 'E-commerce', 'large', 'Chicago, IL', 2005),
    ('Evergreen Logistics', 'Supply Chain', 'medium', 'Denver, CO', 2009),
    ('Lumen Edtech', 'Education Technology', 'small', 'Remote', 2016),
    ('Pinnacle Cybersecurity', 'Cybersecurity', 'medium', 'Washington, DC', 2013),
    ('Orbit Gaming Studios', 'Gaming & Entertainment', 'small', 'Los Angeles, CA', 2019),
    ('Meridian Biotech', 'Biotechnology', 'large', 'San Diego, CA', 2002),
    ('Cascade Renewable Energy', 'Clean Energy', 'medium', 'Portland, OR', 2015),
    ('Fairwind Insurance', 'Insurance', 'enterprise', 'Hartford, CT', 1987),
    ('Skyline Media Group', 'Media & Publishing', 'medium', 'New York, NY', 2007),
    ('Anchor Point Consulting', 'Consulting', 'small', 'Remote', 2017),
    ('Bright Bloom Foods', 'Consumer Goods', 'medium', 'Minneapolis, MN', 2010),
    ('Quantum Leap AI', 'Artificial Intelligence', 'startup', 'San Francisco, CA', 2022),
    ('Redstone Manufacturing', 'Manufacturing', 'large', 'Detroit, MI', 1975),
    ('Bluepeak Telecom', 'Telecommunications', 'enterprise', 'Dallas, TX', 1995),
    ('Ivy & Oak Real Estate Tech', 'Real Estate Technology', 'small', 'Bengaluru, India', 2019),
]

LOCATIONS = [
    'San Francisco, CA', 'New York, NY', 'Austin, TX', 'Seattle, WA', 'Boston, MA',
    'Chicago, IL', 'Denver, CO', 'Los Angeles, CA', 'Washington, DC', 'Remote',
    'Bangalore, India', 'London, UK', 'Toronto, Canada', 'Berlin, Germany', 'Hyderabad, India',
]

JOB_TITLE_TEMPLATES = {
    'Software Engineering': [
        'Backend Engineer', 'Frontend Engineer', 'Full-Stack Developer', 'Software Engineer II',
        'Senior Software Engineer', 'Staff Software Engineer', 'Mobile Engineer (iOS)',
        'Mobile Engineer (Android)', 'Platform Engineer',
    ],
    'Data Science & Analytics': [
        'Data Analyst', 'Data Scientist', 'Senior Data Scientist', 'Business Intelligence Analyst',
        'Analytics Engineer', 'Quantitative Analyst',
    ],
    'Machine Learning & AI': [
        'Machine Learning Engineer', 'AI Research Scientist', 'NLP Engineer', 'Computer Vision Engineer',
        'MLOps Engineer', 'Applied Scientist',
    ],
    'Product Management': [
        'Product Manager', 'Senior Product Manager', 'Associate Product Manager',
        'Group Product Manager', 'Technical Product Manager',
    ],
    'Design (UX/UI)': [
        'UX Designer', 'UI Designer', 'Product Designer', 'Senior Product Designer', 'UX Researcher',
    ],
    'DevOps & Cloud': [
        'DevOps Engineer', 'Site Reliability Engineer', 'Cloud Engineer', 'Platform Reliability Engineer',
        'Infrastructure Engineer',
    ],
    'Cybersecurity': [
        'Security Engineer', 'Security Analyst', 'Penetration Tester', 'GRC Analyst',
        'Cloud Security Engineer',
    ],
    'Sales & Business Development': [
        'Account Executive', 'Sales Development Representative', 'Business Development Manager',
        'Enterprise Account Manager',
    ],
    'Marketing': [
        'Growth Marketing Manager', 'Content Marketing Manager', 'SEO Specialist',
        'Performance Marketing Analyst', 'Brand Marketing Manager',
    ],
    'Human Resources': [
        'HR Business Partner', 'Talent Acquisition Specialist', 'People Operations Manager',
        'Recruiter',
    ],
}

CATEGORY_SKILLS = {
    'Software Engineering': ['Python', 'JavaScript', 'TypeScript', 'React', 'Django', 'Node.js', 'SQL', 'Git', 'REST APIs', 'System Design'],
    'Data Science & Analytics': ['Python', 'SQL', 'Pandas', 'Statistics', 'Data Visualization', 'Tableau', 'Power BI', 'A/B Testing'],
    'Machine Learning & AI': ['Python', 'Machine Learning', 'Deep Learning', 'TensorFlow', 'PyTorch', 'Statistics', 'Data Engineering'],
    'Product Management': ['Agile/Scrum', 'Communication', 'Leadership', 'Problem Solving', 'Project Management', 'A/B Testing'],
    'Design (UX/UI)': ['Figma', 'User Research', 'Communication', 'Problem Solving'],
    'DevOps & Cloud': ['AWS', 'Google Cloud Platform', 'Azure', 'Docker', 'Kubernetes', 'Terraform', 'CI/CD', 'Cloud Architecture'],
    'Cybersecurity': ['Cybersecurity', 'Penetration Testing', 'Network Security', 'CISSP', 'Cloud Architecture'],
    'Sales & Business Development': ['Salesforce', 'Negotiation', 'Communication', 'Leadership'],
    'Marketing': ['SEO', 'Content Strategy', 'Data Visualization', 'Communication', 'A/B Testing'],
    'Human Resources': ['Communication', 'Leadership', 'Project Management', 'Negotiation'],
}

EXPERIENCE_LEVELS = ['entry', 'mid', 'senior', 'lead', 'executive']
EMPLOYMENT_TYPES = ['full_time', 'part_time', 'contract', 'internship', 'freelance']
REMOTE_OPTIONS = ['onsite', 'hybrid', 'remote']

BASE_SALARY_BY_LEVEL = {
    'entry': 55000, 'mid': 85000, 'senior': 120000, 'lead': 150000, 'executive': 190000,
}

SAMPLE_USERS = [
    ('alex_dev', 'Alex', 'Rivera', 'alex@example.com'),
    ('priya_data', 'Priya', 'Nair', 'priya@example.com'),
    ('jordan_pm', 'Jordan', 'Lee', 'jordan@example.com'),
    ('sam_ux', 'Sam', 'Okafor', 'sam@example.com'),
    ('taylor_ml', 'Taylor', 'Chen', 'taylor@example.com'),
]

DESCRIPTION_TEMPLATE = (
    "We are looking for a {title} to join our {category} team at {company}. "
    "You'll work closely with cross-functional partners to design, build, and ship "
    "high-impact work in a {remote} environment. This is a {level_label} role based "
    "in {location}.\n\n"
    "What you'll do:\n"
    "- Own projects end-to-end, from scoping through delivery\n"
    "- Collaborate with engineering, design, and product stakeholders\n"
    "- Continuously improve our processes, tooling, and outcomes\n"
    "- Mentor teammates and contribute to a strong team culture"
)

RESPONSIBILITIES_TEMPLATE = (
    "- Partner with stakeholders to define goals and success metrics\n"
    "- Deliver high-quality work on a predictable cadence\n"
    "- Participate in planning, reviews, and retrospectives\n"
    "- Document decisions and share learnings with the broader team"
)

REQUIREMENTS_TEMPLATE = (
    "- Relevant experience for a {level_label} role\n"
    "- Strong communication and collaboration skills\n"
    "- Comfort working in a fast-paced, ambiguous environment\n"
    "- A track record of delivering measurable outcomes"
)


class Command(BaseCommand):
    help = 'Seed the database with realistic sample data: categories, skills, companies, jobs, users, and analytics snapshots.'

    def add_arguments(self, parser):
        parser.add_argument('--jobs', type=int, default=180, help='Number of job postings to create')
        parser.add_argument('--flush', action='store_true', help='Delete existing seeded data before seeding')

    def handle(self, *args, **options):
        random.seed(42)
        n_jobs = options['jobs']

        if options['flush']:
            self.stdout.write('Flushing existing data...')
            JobPosting.objects.all().delete()
            Company.objects.all().delete()
            JobCategory.objects.all().delete()
            Skill.objects.all().delete()
            SkillDemandSnapshot.objects.all().delete()
            SalaryTrendSnapshot.objects.all().delete()

        with transaction.atomic():
            categories = self._seed_categories()
            skills = self._seed_skills()
            companies = self._seed_companies()
            jobs = self._seed_jobs(n_jobs, categories, companies, skills)
            self._seed_users_and_profiles(skills)
            self._seed_employer_account(companies)
            self._seed_saved_and_applications(jobs)
            self._seed_reviews(companies)
            self._seed_analytics_snapshots(categories, skills)

        self.stdout.write(self.style.SUCCESS(
            f'Seed complete: {JobCategory.objects.count()} categories, '
            f'{Skill.objects.count()} skills, {Company.objects.count()} companies, '
            f'{JobPosting.objects.count()} jobs, {User.objects.count()} users.'
        ))
        self.stdout.write(self.style.WARNING(
            'Sample job-seeker login: username="alex_dev" password="JobPulse2024!" (all sample users share '
            'this password). Sample employer login: username="jamie_recruiter", same password — already owns '
            'a company and can post jobs immediately.'
        ))

    # -- Seeding steps -----------------------------------------------------

    def _seed_categories(self):
        categories = {}
        for name, icon, desc in CATEGORIES:
            obj, _ = JobCategory.objects.get_or_create(
                name=name, defaults={'icon': icon, 'description': desc}
            )
            categories[name] = obj
        self.stdout.write(f'  Categories: {len(categories)}')
        return categories

    def _seed_skills(self):
        skills = {}
        for name, skill_type in SKILLS:
            obj, _ = Skill.objects.get_or_create(name=name, defaults={'skill_type': skill_type})
            skills[name] = obj
        self.stdout.write(f'  Skills: {len(skills)}')
        return skills

    def _seed_companies(self):
        companies = []
        for name, industry, size, hq, founded in COMPANIES:
            obj, _ = Company.objects.get_or_create(
                name=name,
                defaults={
                    'industry': industry, 'size': size, 'headquarters': hq,
                    'founded_year': founded,
                    'website': f"https://www.{name.lower().split()[0]}.example.com",
                    'description': f"{name} is a {industry.lower()} company headquartered in {hq}, "
                                    f"building products that help teams move faster.",
                },
            )
            companies.append(obj)
        self.stdout.write(f'  Companies: {len(companies)}')
        return companies

    def _seed_jobs(self, n_jobs, categories, companies, skills):
        jobs = []
        today = timezone.now()

        for i in range(n_jobs):
            category_name = random.choice(list(CATEGORIES))[0]
            category = categories[category_name]
            title = random.choice(JOB_TITLE_TEMPLATES[category_name])
            company = random.choice(companies)
            location = random.choice(LOCATIONS)
            level = random.choices(EXPERIENCE_LEVELS, weights=[25, 35, 25, 10, 5])[0]
            employment_type = random.choices(EMPLOYMENT_TYPES, weights=[75, 5, 12, 5, 3])[0]
            remote = random.choices(REMOTE_OPTIONS, weights=[35, 30, 35])[0]
            if location == 'Remote':
                remote = 'remote'

            base = BASE_SALARY_BY_LEVEL[level]
            variance = random.uniform(0.85, 1.25)
            salary_min = int(base * variance / 500) * 500
            salary_max = int(salary_min * random.uniform(1.15, 1.45) / 500) * 500

            level_label = dict(JobPosting.ExperienceLevel.choices)[level]
            description = DESCRIPTION_TEMPLATE.format(
                title=title, category=category_name, company=company.name,
                remote=dict(JobPosting.RemoteOption.choices)[remote],
                level_label=level_label, location=location,
            )
            requirements = REQUIREMENTS_TEMPLATE.format(level_label=level_label)

            days_ago = random.randint(0, 120)
            posted_at = today - timedelta(days=days_ago)

            job = JobPosting(
                title=title, company=company, category=category, description=description,
                responsibilities=RESPONSIBILITIES_TEMPLATE, requirements=requirements,
                location=location, remote_option=remote, experience_level=level,
                employment_type=employment_type, salary_min=salary_min, salary_max=salary_max,
                currency='USD', source=random.choice(['JobPulse Direct', 'Partner Network', 'Company Careers Page']),
                is_active=random.random() > 0.08,
                is_featured=random.random() > 0.85,
                views_count=random.randint(5, 2500),
                expires_at=(today + timedelta(days=random.randint(10, 60))).date(),
            )
            job.posted_at = posted_at
            job.save()
            JobPosting.objects.filter(pk=job.pk).update(posted_at=posted_at)

            candidate_skill_names = CATEGORY_SKILLS.get(category_name, list(skills.keys())[:8])
            chosen = random.sample(candidate_skill_names, k=min(len(candidate_skill_names), random.randint(3, 6)))
            for idx, skill_name in enumerate(chosen):
                importance = 'required' if idx < 2 else random.choice(['required', 'preferred', 'nice_to_have'])
                JobSkill.objects.create(job=job, skill=skills[skill_name], importance=importance)

            jobs.append(job)

        self.stdout.write(f'  Jobs: {len(jobs)}')
        return jobs

    def _seed_users_and_profiles(self, skills):
        skill_pool = list(skills.values())
        for username, first, last, email in SAMPLE_USERS:
            user, created = User.objects.get_or_create(
                username=username, defaults={'first_name': first, 'last_name': last, 'email': email}
            )
            if created:
                user.set_password('JobPulse2024!')
                user.save()

            profile, _ = Profile.objects.get_or_create(user=user)
            desired_role = random.choice([t for titles in JOB_TITLE_TEMPLATES.values() for t in titles])
            profile.headline = f"{random.choice(['Aspiring', 'Experienced', 'Passionate'])} {desired_role}"
            profile.bio = f"{first} is exploring new opportunities and open to {random.choice(['remote', 'hybrid', 'onsite'])} roles."
            profile.desired_role = desired_role
            profile.desired_location = random.choice(LOCATIONS)
            profile.experience_level = random.choice(EXPERIENCE_LEVELS)
            profile.open_to_remote = True
            profile.expected_salary = random.choice([60000, 80000, 95000, 120000, 140000])
            profile.save()
            profile.skills.set(random.sample(skill_pool, k=6))

        # Make the first sample user's profile public so the share-profile
        # feature has something to look at immediately after seeding.
        first_user = User.objects.get(username=SAMPLE_USERS[0][0])
        first_user.profile.is_public = True
        first_user.profile.save()

        self.stdout.write(f'  Sample users: {len(SAMPLE_USERS)}')

    def _seed_employer_account(self, companies):
        """Create one sample employer account that owns an existing seeded
        company, so the employer/recruiter flow is demoable immediately."""
        user, created = User.objects.get_or_create(
            username='jamie_recruiter',
            defaults={'first_name': 'Jamie', 'last_name': 'Torres', 'email': 'jamie@example.com'},
        )
        if created:
            user.set_password('JobPulse2024!')
            user.save()

        profile, _ = Profile.objects.get_or_create(user=user)
        profile.role = 'employer'
        profile.headline = 'Talent Acquisition Lead'
        profile.save()

        if companies:
            company = companies[0]
            company.owner = user
            company.save(update_fields=['owner'])

        self.stdout.write(f'  Sample employer account: jamie_recruiter (owns "{companies[0].name}")' if companies else '  Sample employer account: jamie_recruiter')

    def _seed_saved_and_applications(self, jobs):
        users = list(User.objects.filter(username__in=[u[0] for u in SAMPLE_USERS]))
        if not jobs or not users:
            return
        saved_count = 0
        applied_count = 0
        for user in users:
            for job in random.sample(jobs, k=min(5, len(jobs))):
                if random.random() > 0.4:
                    SavedJob.objects.get_or_create(user=user, job=job)
                    saved_count += 1
            for job in random.sample(jobs, k=min(3, len(jobs))):
                if random.random() > 0.5:
                    Application.objects.get_or_create(
                        user=user, job=job,
                        defaults={'status': random.choice(Application.Status.values)},
                    )
                    applied_count += 1
        self.stdout.write(f'  Saved jobs: {saved_count}, Applications: {applied_count}')

    def _seed_reviews(self, companies):
        users = list(User.objects.filter(username__in=[u[0] for u in SAMPLE_USERS]))
        count = 0
        review_bodies = [
            "Great culture and supportive management. Growth opportunities are plentiful.",
            "Solid work-life balance, though the onboarding process could be smoother.",
            "Talented team and interesting problems to solve day to day.",
            "Compensation is competitive; the interview process was thorough but fair.",
            "Leadership is transparent about company direction and challenges.",
        ]
        for company in random.sample(companies, k=min(10, len(companies))):
            for user in random.sample(users, k=min(2, len(users))):
                _, created = JobReview.objects.get_or_create(
                    company=company, user=user,
                    defaults={
                        'rating': random.randint(3, 5),
                        'title': random.choice(['Great place to grow', 'Solid team', 'Good experience overall',
                                                 'Would recommend', 'Positive experience']),
                        'body': random.choice(review_bodies),
                    },
                )
                if created:
                    count += 1
        self.stdout.write(f'  Company reviews: {count}')

    def _seed_analytics_snapshots(self, categories, skills):
        today = timezone.now().date().replace(day=1)
        months = [today - timedelta(days=30 * i) for i in range(11, -1, -1)]

        skill_snap_count = 0
        for skill in skills.values():
            base_demand = random.randint(5, 60)
            trend = random.uniform(-0.03, 0.08)
            for i, period in enumerate(months):
                job_count = max(0, int(base_demand * (1 + trend) ** i + random.randint(-3, 3)))
                avg_salary = random.randint(60000, 160000)
                SkillDemandSnapshot.objects.update_or_create(
                    skill=skill, period=period,
                    defaults={'job_count': job_count, 'avg_salary': avg_salary},
                )
                skill_snap_count += 1

        salary_snap_count = 0
        for category in categories.values():
            base = random.randint(70000, 150000)
            for location in random.sample(LOCATIONS, k=5):
                for i, period in enumerate(months):
                    drift = random.uniform(-0.01, 0.02)
                    mid = int(base * (1 + drift) ** i)
                    SalaryTrendSnapshot.objects.update_or_create(
                        category=category, location=location, period=period,
                        defaults={
                            'avg_salary': mid,
                            'min_salary': int(mid * 0.8),
                            'max_salary': int(mid * 1.25),
                            'job_count': random.randint(2, 40),
                        },
                    )
                    salary_snap_count += 1

        self.stdout.write(f'  Skill demand snapshots: {skill_snap_count}, Salary trend snapshots: {salary_snap_count}')
