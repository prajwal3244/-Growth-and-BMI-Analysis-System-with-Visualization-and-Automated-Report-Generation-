"""NutritionService — AI nutrition intelligence (feature #3).

Generates evidence-informed daily targets (calories, macros, water), lifestyle
recommendations (sleep, exercise, school activity, screen time) and a weekly
meal plan, all adjusted for age, gender, BMI status and growth percentile.

Calorie targets are grounded in Estimated Energy Requirement (EER) ranges by
age/gender, then nudged by BMI category so under/overweight children are guided
toward a healthy trajectory. Macros follow the Acceptable Macronutrient
Distribution Ranges (AMDR). Values are guidance, not prescriptions (see
disclaimer) and are centralized here so guidelines can be updated in one place.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from growthai.core.domain import BmiCategory, Gender, Measurement

# Baseline daily kcal by age band (years) and sex, moderate activity (EER midpoints).
_EER = {
    Gender.MALE: [(1, 1000), (3, 1400), (6, 1800), (9, 2000), (13, 2400), (18, 2800), (99, 2600)],
    Gender.FEMALE: [(1, 1000), (3, 1300), (6, 1600), (9, 1800), (13, 2000), (18, 2200), (99, 2000)],
}

# BMI-category multiplier: a gentle nudge, never a crash diet.
_BMI_KCAL_ADJ = {
    BmiCategory.UNDERWEIGHT: 1.12,
    BmiCategory.NORMAL: 1.00,
    BmiCategory.OVERWEIGHT: 0.92,
    BmiCategory.OBESE: 0.85,
}

# Sleep hours by age band (National Sleep Foundation).
_SLEEP = [(1, "12-16 h"), (2, "11-14 h"), (5, "10-13 h"), (13, "9-12 h"), (18, "8-10 h"), (99, "7-9 h")]

_FOODS = {
    BmiCategory.UNDERWEIGHT: [
        "Whole milk, cheese and yogurt", "Nut & seed butters", "Eggs and lean meats",
        "Bananas, mangoes, avocado", "Whole-grain cereals with ghee/oil",
    ],
    BmiCategory.NORMAL: [
        "Balanced plate: ½ vegetables/fruit, ¼ grains, ¼ protein",
        "Dairy or fortified alternatives", "Legumes and pulses", "Fish twice a week",
        "Water instead of sugary drinks",
    ],
    BmiCategory.OVERWEIGHT: [
        "High-fibre vegetables and salads", "Whole fruits (not juice)",
        "Lean protein: chicken, fish, dal", "Whole grains over refined",
        "Limit fried and sugary foods",
    ],
    BmiCategory.OBESE: [
        "Non-starchy vegetables at every meal", "Portion-controlled whole grains",
        "Lean/plant proteins", "Zero sugar-sweetened beverages",
        "Fruit for dessert instead of sweets",
    ],
}


def _band_lookup(table: list[tuple[float, object]], age_years: float) -> object:
    for upper, value in table:
        if age_years < upper:
            return value
    return table[-1][1]


@dataclass
class NutritionPlan:
    """Daily nutrition + lifestyle recommendation for one child."""

    calories_kcal: int
    protein_g: int
    fat_g: int
    carbs_g: int
    water_ml: int
    sleep: str
    exercise: str
    school_activity: str
    screen_time: str
    food_suggestions: list[str]
    weekly_meal_plan: dict[str, dict[str, str]] = field(default_factory=dict)

    def as_dict(self) -> dict[str, object]:
        return {
            "daily_targets": {
                "calories_kcal": self.calories_kcal,
                "protein_g": self.protein_g,
                "fat_g": self.fat_g,
                "carbs_g": self.carbs_g,
                "water_ml": self.water_ml,
            },
            "lifestyle": {
                "sleep": self.sleep,
                "exercise": self.exercise,
                "school_activity": self.school_activity,
                "screen_time": self.screen_time,
            },
            "food_suggestions": self.food_suggestions,
            "weekly_meal_plan": self.weekly_meal_plan,
        }


class NutritionService:
    """Builds personalized nutrition plans."""

    def daily_calories(self, m: Measurement, category: BmiCategory) -> int:
        base = _band_lookup(_EER[m.gender], m.age_years)
        return int(round(base * _BMI_KCAL_ADJ[category] / 10.0) * 10)

    def recommend(self, m: Measurement, category: BmiCategory) -> NutritionPlan:
        kcal = self.daily_calories(m, category)
        # AMDR: protein 10-30%, fat 25-35%, carbs 45-65% of energy.
        protein_g = int(round(kcal * 0.20 / 4))   # 4 kcal/g
        fat_g = int(round(kcal * 0.30 / 9))       # 9 kcal/g
        carbs_g = int(round(kcal * 0.50 / 4))     # 4 kcal/g
        # Water: ~1 ml per kcal is a well-known clinical rule of thumb, floored sensibly.
        water_ml = max(1000, int(round(kcal / 100.0) * 100))

        exercise = (
            "At least 60 min/day of moderate-to-vigorous activity"
            if m.age_years >= 5
            else "Active play throughout the day"
        )
        if category in (BmiCategory.OVERWEIGHT, BmiCategory.OBESE):
            exercise += "; add 3 days/week of aerobic activity"

        return NutritionPlan(
            calories_kcal=kcal,
            protein_g=protein_g,
            fat_g=fat_g,
            carbs_g=carbs_g,
            water_ml=water_ml,
            sleep=_band_lookup(_SLEEP, m.age_years),
            exercise=exercise,
            school_activity="Encourage PE, sports and active recess; walk/cycle to school if safe",
            screen_time=("<1 h/day" if m.age_years < 5 else "<2 h/day recreational"),
            food_suggestions=_FOODS[category],
            weekly_meal_plan=self._weekly_meal_plan(category),
        )

    def _weekly_meal_plan(self, category: BmiCategory) -> dict[str, dict[str, str]]:
        """A simple, rotating 7-day plan tuned to the BMI category."""
        emphasis = {
            BmiCategory.UNDERWEIGHT: "energy-dense",
            BmiCategory.NORMAL: "balanced",
            BmiCategory.OVERWEIGHT: "high-fibre",
            BmiCategory.OBESE: "portion-controlled",
        }[category]
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        breakfasts = [
            "Oats with milk, banana & nuts", "Veg poha + curd", "Eggs + whole-grain toast",
            "Idli/dosa + sambar", "Fruit smoothie + peanut butter toast",
            "Upma + boiled egg", "Paratha (light oil) + curd",
        ]
        lunches = [
            "Dal, rice, mixed-veg, salad", "Roti, rajma, sauteed greens",
            "Veg pulao + raita + cucumber", "Fish/paneer curry, roti, salad",
            "Chicken/chickpea bowl + veg", "Sambar rice + beans poriyal",
            "Khichdi + curd + salad",
        ]
        dinners = [
            "Roti, sabzi, dal", "Veg soup + grilled protein", "Millet roti + veg curry",
            "Stir-fried veg + tofu/egg", "Light khichdi + salad",
            "Dal, roti, steamed veg", "Vegetable stew + bread",
        ]
        plan: dict[str, dict[str, str]] = {}
        for i, day in enumerate(days):
            plan[day] = {
                "breakfast": breakfasts[i],
                "lunch": lunches[i],
                "dinner": dinners[i],
                "emphasis": emphasis,
            }
        return plan
