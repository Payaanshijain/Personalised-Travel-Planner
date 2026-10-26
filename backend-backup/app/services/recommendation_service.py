"""
Personalized Recommendation Service (Activity 3.3).
Categorizes, filters, and ranks recommendations tailored to user preferences:
interests, dietary restrictions, mobility constraints, pace, budget, and travel style.
"""

from typing import Dict, List, Any
from app.schemas.trips import RecommendationItem, CategorizedRecommendationsResponse


def generate_personalized_recommendations(trip: Dict[str, Any]) -> CategorizedRecommendationsResponse:
    destination = trip.get("destination", "Your Destination")
    interests = [i.strip().lower() for i in trip.get("interests", [])]
    dietary = trip.get("dietary_preference", "No preference").lower()
    pace = trip.get("travel_pace", "Moderate").lower()
    mobility = trip.get("mobility_requirements", "None").lower()
    budget = float(trip.get("budget", 1000.0))
    traveller_count = max(1, int(trip.get("traveller_count", 1)))
    currency = trip.get("currency", "USD")
    budget_per_person = budget / traveller_count

    has_mobility_concern = "none" not in mobility and len(mobility) > 1

    categories: Dict[str, List[RecommendationItem]] = {
        "Attractions & Sightseeing": [],
        "Food & Dining": [],
        "Nature & Outdoor": [],
        "Cultural & Historical": [],
        "Adventure Activities": [],
        "Relaxation & Leisure": [],
    }

    # 1. Attractions & Sightseeing
    reasons = ["Top destination highlight"]
    if "shopping" in interests:
        reasons.append("Matches your Shopping interest")
    if "beaches" in interests:
        reasons.append("Matches your Beaches interest")

    categories["Attractions & Sightseeing"].append(
        RecommendationItem(
            title=f"Iconic Landmarks & Central Promenade of {destination}",
            category="Attractions & Sightseeing",
            description=f"Explore the celebrated architectural and landmark core of {destination}. "
                        f"{'Step-free walkways and accessible resting points are available.' if has_mobility_concern else 'Easily navigable on foot or via public transit.'}",
            estimated_cost=f"Free - 25 {currency}",
            duration="2-3 hours",
            location=f"Central {destination}",
            match_reasons=reasons,
            is_verified=False,
        )
    )

    if "beaches" in interests or "nature" in interests:
        categories["Attractions & Sightseeing"].append(
            RecommendationItem(
                title=f"{destination} Coastal Scenic Viewpoint",
                category="Attractions & Sightseeing",
                description=f"Panoramic vistas overlooking {destination}'s most scenic natural horizons, suitable for evening sunset viewing.",
                estimated_cost="Free",
                duration="1-2 hours",
                location=f"Coast / Lookout Point, {destination}",
                match_reasons=["Matches your Beach/Nature interest", "Scenic relaxation"],
                is_verified=False,
            )
        )

    # 2. Food & Dining (Personalized to dietary mandate)
    dining_reasons = [f"Tailored to your {trip.get('dietary_preference')} preference"]
    if "food" in interests:
        dining_reasons.append("Curated for Food enthusiasts")

    if "jain" in dietary:
        dining_title = f"Pure Vegetarian & Jain Culinary Haven in {destination}"
        dining_desc = "Curated kitchen strictly offering no-onion, no-garlic, no-root-vegetable dishes prepared according to Jain dietary customs."
    elif "vegan" in dietary:
        dining_title = f"Artisanal Plant-Based & Vegan Kitchen in {destination}"
        dining_desc = "Organic, certified vegan eatery featuring creative plant-based interpretations of local dishes without dairy or animal products."
    elif "vegetarian" in dietary:
        dining_title = f"Traditional Vegetarian Dining in {destination}"
        dining_desc = "Highly rated specialty vegetarian dining highlighting regional recipes, fresh produce, and wholesome meals."
    else:
        dining_title = f"Authentic Regional Gourmet Experience in {destination}"
        dining_desc = f"Celebrated bistro serving local specialties of {destination} with seasonal ingredients."

    cost_estimate = f"15-35 {currency} per person" if budget_per_person < 500 else f"35-70 {currency} per person"

    categories["Food & Dining"].append(
        RecommendationItem(
            title=dining_title,
            category="Food & Dining",
            description=dining_desc,
            estimated_cost=cost_estimate,
            duration="1.5 hours",
            location=f"Culinary Quarter, {destination}",
            match_reasons=dining_reasons,
            is_verified=False,
        )
    )

    # 3. Cultural & Historical
    if "history" in interests or "culture" in interests or "spiritual places" in interests:
        hist_reasons = []
        if "history" in interests:
            hist_reasons.append("Matches your History interest")
        if "culture" in interests:
            hist_reasons.append("Matches your Culture interest")
        if "spiritual places" in interests:
            hist_reasons.append("Matches your Spiritual Places interest")

        categories["Cultural & Historical"].append(
            RecommendationItem(
                title=f"Heritage Museum & Historic Quarter of {destination}",
                category="Cultural & Historical",
                description=f"Discover centuries of heritage, art, and historical artifacts that shaped {destination}. "
                            f"{'Offers elevator access and wheelchair ramps.' if has_mobility_concern else 'Audio-guided walking tour available.'}",
                estimated_cost=f"10-20 {currency}",
                duration="2.5 hours",
                location=f"Old Town, {destination}",
                match_reasons=hist_reasons if hist_reasons else ["Cultural enrichment"],
                is_verified=False,
            )
        )

    # 4. Nature & Outdoor
    if "nature" in interests or "adventure" in interests or "relaxation" in interests:
        nature_desc = f"Lush botanical reserve with peaceful walking trails."
        if has_mobility_concern:
            nature_desc += " Paved, flat accessible pathways with seating every 100 meters."
        else:
            nature_desc += " Gentle loop trails offering scenic flora and tranquil birdwatching."

        categories["Nature & Outdoor"].append(
            RecommendationItem(
                title=f"{destination} Botanical Gardens & Green Sanctuary",
                category="Nature & Outdoor",
                description=nature_desc,
                estimated_cost=f"5-15 {currency}",
                duration="2 hours",
                location=f"Green Belt, {destination}",
                match_reasons=["Nature retreat", "Calm outdoor environment"],
                is_verified=False,
            )
        )

    # 5. Adventure Activities
    if "adventure" in interests:
        if has_mobility_concern:
            categories["Adventure Activities"].append(
                RecommendationItem(
                    title=f"Accessible Panoramic Cable Car / Harbour Cruise in {destination}",
                    category="Adventure Activities",
                    description=f"Gentle, exhilarating scenic transit experience offering breathtaking 360-degree views with full ramp and step-free accessibility.",
                    estimated_cost=f"25-45 {currency}",
                    duration="1.5 hours",
                    location=f"Scenic Terminal, {destination}",
                    match_reasons=["Accessible adventure", "Matches your Adventure interest"],
                    is_verified=False,
                )
            )
        else:
            categories["Adventure Activities"].append(
                RecommendationItem(
                    title=f"Guided Outdoor Adventure & Trek in {destination}",
                    category="Adventure Activities",
                    description=f"Action-packed outdoor excursion tailored for adventurous travelers, led by certified local wilderness guides.",
                    estimated_cost=f"40-80 {currency}",
                    duration="4 hours",
                    location=f"Outskirts of {destination}",
                    match_reasons=["High-energy adventure", "Matches your Adventure interest"],
                    is_verified=False,
                )
            )

    # 6. Relaxation & Leisure
    relax_reasons = []
    if "relaxation" in interests:
        relax_reasons.append("Matches your Relaxation interest")
    if "relaxed" in pace:
        relax_reasons.append("Aligned with your Relaxed travel pace")

    categories["Relaxation & Leisure"].append(
        RecommendationItem(
            title=f"Serene Artisan Tea & Sunset Lounge in {destination}",
            category="Relaxation & Leisure",
            description=f"Quiet, contemplative atmosphere to decompress, enjoy fine tea or coffee, and read in a peaceful ambiance.",
            estimated_cost=f"8-20 {currency}",
            duration="1-2 hours",
            location=f"Riverside / Garden District, {destination}",
            match_reasons=relax_reasons if relax_reasons else ["Leisure downtime"],
            is_verified=False,
        )
    )

    # Filter out empty categories
    filtered_categories = {k: v for k, v in categories.items() if len(v) > 0}
    total_count = sum(len(items) for items in filtered_categories.values())

    return CategorizedRecommendationsResponse(
        trip_id=str(trip.get("id", "")),
        destination=destination,
        categories=filtered_categories,
        total_recommendations=total_count,
    )
