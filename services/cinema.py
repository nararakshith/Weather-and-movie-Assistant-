class MovieGuide:
    """Small curated guide to Indian films grouped by broad genre."""

    _titles = {
        "action": ("Jawan", "RRR", "Pushpa: The Rise"),
        "comedy": ("Laapataa Ladies", "Delhi Belly", "Dhamaal"),
        "drama": ("12th Fail", "Dangal", "The Lunchbox"),
        "family": ("English Vinglish", "Secret Superstar", "Chillar Party"),
        "horror": ("Tumbbad", "Stree", "Bhoot"),
        "romance": ("Sita Ramam", "Jab We Met", "Veer-Zaara"),
        "sci-fi": ("Koi... Mil Gaya", "Cargo", "Robot"),
        "thriller": ("Andhadhun", "Kahaani", "Drishyam"),
    }

    def recommend(self, genre: str) -> str:
        category = " ".join(genre.casefold().replace("-", " ").split())
        category = {"science fiction": "sci fi", "romantic": "romance"}.get(category, category)
        category = {"sci fi": "sci-fi"}.get(category, category)
        titles = self._titles.get(category)
        if not titles:
            supported = ", ".join(self._titles)
            return f"I don't have a list for that genre yet. Try one of these: {supported}."
        return f"{category.title()} picks: " + ", ".join(titles) + "."
