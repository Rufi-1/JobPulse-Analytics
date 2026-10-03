"""
Rule-based intelligence layer for JobPulse Analytics.

Everything here is deterministic, explainable logic — no external AI/ML
service or network call is required. Two capabilities are provided:

1. ``predict_salary``   — estimates a salary range for a role, given
   location, experience level and a set of skills, blending live
   marketplace data (when available) with a hand-tuned baseline model.

2. ``recommend_jobs_for_profile`` / ``job_match_score`` — scores how well
   a user's profile (skills, desired role/location/salary, experience)
   fits each open job posting, so the platform can surface personalized
   recommendations without any third-party AI.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from django.db.models import Avg, Count, Q

# ---------------------------------------------------------------------------
# Baseline compensation model
# ---------------------------------------------------------------------------

# Base annual salary (USD) by experience level — used when no historical
# data exists yet for a given category/location combination.
EXPERIENCE_BASE_SALARY = {
    'entry': 58000,
    'mid': 85000,
    'senior': 122000,
    'lead': 155000,
    'executive': 195000,
}

# Simple cost-of-living / demand multiplier for well-known tech hubs.
# Any location not listed falls back to 1.0 (national average).
LOCATION_MULTIPLIERS = {
    'san francisco': 1.55, 'new york': 1.42, 'seattle': 1.30, 'boston': 1.22,
    'austin': 1.12, 'los angeles': 1.20, 'chicago': 1.10, 'denver': 1.08,
    'washington dc': 1.18, 'bangalore': 0.35, 'bengaluru': 0.35, 'mumbai': 0.34,
    'delhi': 0.32, 'hyderabad': 0.33, 'pune': 0.31, 'london': 1.25,
    'toronto': 1.05, 'berlin': 0.95, 'remote': 1.05,
}

# High-value skills add a premium to the predicted salary (per matched skill,
# capped). Values are illustrative percentages of the base salary.
PREMIUM_SKILLS = {
    'machine learning': 0.10, 'kubernetes': 0.08, 'aws': 0.07, 'react': 0.05,
    'golang': 0.08, 'rust': 0.09, 'terraform': 0.07, 'data engineering': 0.09,
    'system design': 0.08, 'security': 0.07, 'cloud architecture': 0.09,
    'python': 0.04, 'sql': 0.03, 'leadership': 0.06,
}

MAX_SKILL_PREMIUM = 0.30  # cap total skill premium at 30% of base


def _location_multiplier(location: str) -> float:
    if not location:
        return 1.0
    key = location.strip().lower()
    for known, mult in LOCATION_MULTIPLIERS.items():
        if known in key:
            return mult
    return 1.0


def _skill_premium(skill_names) -> float:
    total = 0.0
    for name in skill_names:
        total += PREMIUM_SKILLS.get(name.strip().lower(), 0.0)
    return min(total, MAX_SKILL_PREMIUM)


@dataclass
class SalaryPrediction:
    predicted_min: int
    predicted_max: int
    predicted_mid: int
    confidence: int
    basis: str
    factors: list = field(default_factory=list)


def predict_salary(category=None, location: str = '', experience_level: str = 'mid',
                    skills=None) -> SalaryPrediction:
    """
    Predict a salary range using a blend of:
      - real aggregated market data (SalaryTrendSnapshot) when enough exists, and
      - a transparent rule-based baseline model as a fallback / floor.
    """
    from analytics.models import SalaryTrendSnapshot

    skills = list(skills or [])
    skill_names = [s.name if hasattr(s, 'name') else str(s) for s in skills]
    factors = []

    base = EXPERIENCE_BASE_SALARY.get(experience_level, EXPERIENCE_BASE_SALARY['mid'])
    factors.append(f"Base salary for '{experience_level}' experience: ${base:,.0f}")

    loc_mult = _location_multiplier(location)
    factors.append(f"Location adjustment for '{location or 'unspecified'}': x{loc_mult:.2f}")

    premium = _skill_premium(skill_names)
    if premium:
        factors.append(f"Skill premium from {len(skill_names)} skill(s): +{premium * 100:.0f}%")

    rule_mid = base * loc_mult * (1 + premium)
    rule_min = rule_mid * 0.85
    rule_max = rule_mid * 1.18

    confidence = 55  # baseline confidence for the rule-based model alone
    basis = 'rule-based baseline model'

    # Blend in historical data if we have it.
    market_qs = SalaryTrendSnapshot.objects.all()
    if category is not None:
        market_qs = market_qs.filter(category=category)
    if location:
        market_qs = market_qs.filter(location__icontains=location.split(',')[0].strip())

    market_stats = market_qs.aggregate(
        avg_avg=Avg('avg_salary'), avg_min=Avg('min_salary'),
        avg_max=Avg('max_salary'), n=Count('id'),
    )

    if market_stats['n'] and market_stats['n'] >= 2 and market_stats['avg_avg']:
        market_min = market_stats['avg_min']
        market_max = market_stats['avg_max']
        market_mid = market_stats['avg_avg']

        # Blend: more historical snapshots -> more weight on real data (up to 70%).
        weight = min(0.70, 0.20 + market_stats['n'] * 0.05)
        blended_min = rule_min * (1 - weight) + market_min * weight
        blended_max = rule_max * (1 - weight) + market_max * weight
        blended_mid = rule_mid * (1 - weight) + market_mid * weight

        confidence = min(92, 55 + market_stats['n'] * 4)
        basis = f'blended with {market_stats["n"]} historical market snapshot(s)'
        factors.append(
            f"Blended {weight * 100:.0f}% with observed market data "
            f"(avg ${market_mid:,.0f}) from {market_stats['n']} data points"
        )
        rule_min, rule_max, rule_mid = blended_min, blended_max, blended_mid

    return SalaryPrediction(
        predicted_min=int(round(rule_min / 500) * 500),
        predicted_max=int(round(rule_max / 500) * 500),
        predicted_mid=int(round(rule_mid / 500) * 500),
        confidence=int(confidence),
        basis=basis,
        factors=factors,
    )


# ---------------------------------------------------------------------------
# Job <-> profile matching
# ---------------------------------------------------------------------------

EXPERIENCE_ORDER = ['entry', 'mid', 'senior', 'lead', 'executive']


def _experience_distance(a: str, b: str) -> int:
    try:
        return abs(EXPERIENCE_ORDER.index(a) - EXPERIENCE_ORDER.index(b))
    except ValueError:
        return 2


def job_match_score(profile, job) -> dict:
    """
    Score how well a single JobPosting matches a user Profile, 0-100.
    Returns a dict with the score and a human-readable breakdown, so the
    UI can explain *why* a job was recommended (transparent, not a black box).
    """
    score = 0.0
    max_score = 0.0
    reasons = []

    # --- Skill overlap (weight: 50) -----------------------------------
    profile_skill_ids = set(profile.skills.values_list('id', flat=True))
    job_skill_weights = {js.skill_id: js.weight for js in job.job_skills.select_related('skill')}
    max_score += 50
    if job_skill_weights:
        total_weight = sum(job_skill_weights.values())
        matched_weight = sum(w for sid, w in job_skill_weights.items() if sid in profile_skill_ids)
        skill_component = 50 * (matched_weight / total_weight) if total_weight else 0
        score += skill_component
        matched_count = len(profile_skill_ids & set(job_skill_weights.keys()))
        if matched_count:
            reasons.append(f"{matched_count} of your skills match this role's requirements")
    else:
        score += 25  # neutral if job lists no skills

    # --- Desired role keyword overlap (weight: 15) ---------------------
    max_score += 15
    if profile.desired_role:
        wanted = set(profile.desired_role.lower().split())
        title_words = set(job.title.lower().split())
        if wanted & title_words:
            score += 15
            reasons.append("Job title matches your desired role")
        elif profile.desired_role.lower() in job.title.lower():
            score += 10

    # --- Location / remote fit (weight: 15) -----------------------------
    max_score += 15
    if job.remote_option == 'remote' and profile.open_to_remote:
        score += 15
        reasons.append("Fully remote — matches your remote preference")
    elif profile.desired_location and profile.desired_location.lower() in job.location.lower():
        score += 15
        reasons.append(f"Located in your preferred location ({profile.desired_location})")
    elif job.remote_option == 'hybrid' and profile.open_to_remote:
        score += 8

    # --- Experience level fit (weight: 10) ------------------------------
    max_score += 10
    distance = _experience_distance(profile.experience_level, job.experience_level)
    exp_component = max(0, 10 - distance * 4)
    score += exp_component
    if distance == 0:
        reasons.append("Experience level matches exactly")

    # --- Salary expectation fit (weight: 10) -----------------------------
    max_score += 10
    if profile.expected_salary and job.salary_mid:
        ratio = job.salary_mid / profile.expected_salary
        if ratio >= 0.9:
            score += 10
            reasons.append("Salary meets or exceeds your expectation")
        elif ratio >= 0.75:
            score += 5

    pct = int(round((score / max_score) * 100)) if max_score else 0
    return {'score': pct, 'reasons': reasons}


def recommend_jobs_for_profile(profile, limit: int = 10):
    """
    Return the top-N open JobPostings for a profile, each annotated with
    ``match_score`` and ``match_reasons``, best matches first.
    """
    from jobs.models import JobPosting

    candidates = (
        JobPosting.objects.filter(is_active=True)
        .select_related('company', 'category')
        .prefetch_related('job_skills__skill')
    )

    # Pre-filter by category-ish overlap to keep this cheap for large tables.
    scored = []
    for job in candidates[:500]:  # sane cap for a rule-based pass
        result = job_match_score(profile, job)
        if result['score'] > 0:
            scored.append((job, result))

    scored.sort(key=lambda pair: pair[1]['score'], reverse=True)
    return scored[:limit]


def trending_skills(limit: int = 10):
    """Return skills ranked by number of currently active job postings requiring them."""
    from jobs.models import Skill
    return (
        Skill.objects.annotate(
            demand=Count('skill_jobs', filter=Q(skill_jobs__job__is_active=True), distinct=True)
        )
        .filter(demand__gt=0)
        .order_by('-demand')[:limit]
    )


# ---------------------------------------------------------------------------
# Personalized market analysis (skill gap + salary position)
# ---------------------------------------------------------------------------

def skill_gap_analysis(profile, limit: int = 8):
    """
    Compare a profile's skills against what's actually in demand for their
    desired role, surfacing high-value skills they're missing.

    Returns a dict with:
      - have: profile's skills, annotated with current market demand
      - missing: highest-demand skills relevant to their desired role that
        the profile does NOT have, sorted by demand
      - role_matched_jobs: how many active postings matched their desired role
        (falls back to all active postings if desired_role is blank or matches nothing)
    """
    from jobs.models import JobPosting, Skill

    profile_skill_ids = set(profile.skills.values_list('id', flat=True))

    qs = JobPosting.objects.filter(is_active=True)
    role_specific = False
    if profile.desired_role:
        q = Q()
        for word in profile.desired_role.split():
            q |= Q(title__icontains=word)
        role_qs = qs.filter(q)
        if role_qs.exists():
            qs = role_qs
            role_specific = True

    demand_qs = (
        Skill.objects.filter(skill_jobs__job__in=qs)
        .annotate(demand=Count('skill_jobs__job', distinct=True))
        .filter(demand__gt=0)
        .order_by('-demand')
    )

    have, missing = [], []
    for skill in demand_qs:
        entry = {'skill': skill, 'demand': skill.demand}
        (have if skill.id in profile_skill_ids else missing).append(entry)

    return {
        'have': have[:limit],
        'missing': missing[:limit],
        'role_matched_jobs': qs.count(),
        'role_specific': role_specific,
    }


def market_position_for_profile(profile):
    """
    Blend the salary-prediction engine with a profile's own expected salary,
    so a user can see how their expectation compares to the current market
    for their skills, location, and experience level.
    """
    prediction = predict_salary(
        category=None,
        location=profile.desired_location,
        experience_level=profile.experience_level,
        skills=profile.skills.all(),
    )
    gap = None
    gap_pct = None
    if profile.expected_salary:
        gap = profile.expected_salary - prediction.predicted_mid
        if prediction.predicted_mid:
            gap_pct = round(gap / prediction.predicted_mid * 100)
    return {'prediction': prediction, 'gap': gap, 'gap_pct': gap_pct}
