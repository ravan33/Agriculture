"""Chatbot service for multilingual agriculture assistance."""
import csv
import json
import logging
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from .market_service import get_market_prices
from .weather_service import generate_weather_advice, get_weather_data

logger = logging.getLogger(__name__)


PRETRAINED_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
INTENT_MODEL_NAME = "facebook/bart-large-mnli"
INDEX_FILE_NAME = "chatbot_index.pkl"

SUPPORTED_RESPONSE_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "te": "Telugu",
    "ta": "Tamil",
    "mr": "Marathi",
    "bn": "Bengali",
    "gu": "Gujarati",
    "kn": "Kannada",
    "pa": "Punjabi",
}


@dataclass
class KnowledgeItem:
    question: str
    answer: str
    suggestions: List[str]


class AgricultureChatbot:
    """Multilingual retrieval chatbot with dynamic agriculture suggestions."""

    def __init__(self, load_models: bool = True) -> None:
        self.model = None
        self.util = None
        self.intent_classifier = None
        self.query_translator = None
        self.answer_translator = None
        self.detect = None
        self.stemmer = None
        self.word_tokenizer = None
        self.vectorizer = None
        self.cosine_similarity = None

        self.knowledge = self._build_knowledge_base()
        self.knowledge_embeddings = None
        self.corpus_docs: List[Dict[str, object]] = []
        self.corpus_matrix = None
        self.response_cache: Dict[str, Dict[str, object]] = {}
        self.base_dir = Path(__file__).resolve().parent.parent
        self.default_external_corpus_dir = self.base_dir / "data" / "agri_corpus"
        self.index_path = self.base_dir / "model" / INDEX_FILE_NAME

        self._initialize_integrations(load_models=load_models)
        self._initialize_corpus_retriever()

    def _initialize_integrations(self, load_models: bool = True) -> None:
        """Initialize optional AI dependencies gracefully."""
        if load_models:
            try:
                from sentence_transformers import SentenceTransformer, util  # type: ignore

                self.model = SentenceTransformer(PRETRAINED_MODEL_NAME)
                self.util = util
                self.knowledge_embeddings = self.model.encode(
                    [item.question for item in self.knowledge],
                    convert_to_tensor=True,
                )
                logger.info("Chatbot model loaded: %s", PRETRAINED_MODEL_NAME)
            except Exception as exc:
                logger.warning("SentenceTransformer unavailable, using fallback: %s", exc)

            try:
                from transformers import pipeline  # type: ignore

                self.intent_classifier = pipeline("zero-shot-classification", model=INTENT_MODEL_NAME)
                logger.info("Intent classifier loaded: %s", INTENT_MODEL_NAME)
            except Exception as exc:
                logger.warning("Transformers classifier unavailable: %s", exc)

        try:
            from nltk.stem import PorterStemmer  # type: ignore
            from nltk.tokenize import regexp_tokenize  # type: ignore

            self.stemmer = PorterStemmer()
            self.word_tokenizer = regexp_tokenize
        except Exception as exc:
            logger.warning("NLTK unavailable: %s", exc)

        try:
            from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore
            from sklearn.metrics.pairwise import cosine_similarity  # type: ignore

            self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=50000)
            self.cosine_similarity = cosine_similarity
        except Exception as exc:
            logger.warning("Scikit retriever unavailable: %s", exc)

        try:
            from langdetect import detect  # type: ignore

            self.detect = detect
        except Exception as exc:
            logger.warning("Language detection unavailable: %s", exc)

        try:
            from deep_translator import GoogleTranslator  # type: ignore

            self.query_translator = GoogleTranslator
            self.answer_translator = GoogleTranslator
        except Exception as exc:
            logger.warning("Translation support unavailable: %s", exc)

    def _initialize_corpus_retriever(self) -> None:
        if self._load_prebuilt_index():
            return

        self.corpus_docs = self._build_large_corpus(external_dir=self.default_external_corpus_dir)
        if not self.vectorizer or not self.corpus_docs:
            return
        try:
            corpus_texts = [str(doc["text"]) for doc in self.corpus_docs]
            self.corpus_matrix = self.vectorizer.fit_transform(corpus_texts)
            logger.info("Chatbot corpus initialized with %s documents", len(corpus_texts))
        except Exception as exc:
            logger.warning("Failed to initialize corpus retriever: %s", exc)

    def _load_prebuilt_index(self) -> bool:
        """Load prebuilt corpus index if available for faster startup."""
        if not self.index_path.exists():
            return False
        try:
            with self.index_path.open("rb") as index_file:
                payload = pickle.load(index_file)

            docs = payload.get("docs")
            vectorizer = payload.get("vectorizer")
            matrix = payload.get("matrix")

            if not docs or vectorizer is None or matrix is None:
                return False

            self.corpus_docs = docs
            self.vectorizer = vectorizer
            self.corpus_matrix = matrix
            logger.info("Loaded chatbot index from %s with %s docs", self.index_path, len(self.corpus_docs))
            return True
        except Exception as exc:
            logger.warning("Failed to load prebuilt chatbot index: %s", exc)
            return False

    def _build_knowledge_base(self) -> List[KnowledgeItem]:
        """Build comprehensive multilingual knowledge base with clear, structured responses."""
        return [
            # Crop Disease Management
            KnowledgeItem(
                question="How do I detect crop disease early?",
                answer="Early disease detection is critical for prevention. Watch for: leaf color changes (yellowing, browning), unusual spots (circular, angular patterns), wilting without water stress, stem softness or discoloration, and abnormal growth. Use clear photos taken in good light and compare daily. Early intervention reduces disease spread and improves recovery rates significantly.",
                suggestions=[
                    "Upload a close leaf image in AI Diagnosis tool",
                    "Document symptoms with date and location",
                    "Isolate visibly infected plants immediately",
                    "Check morning and evening for progression",
                ],
            ),
            KnowledgeItem(
                question="Tomato disease prevention and management guide",
                answer="Tomato diseases include early blight (brown spots), late blight (water-soaked lesions), and bacterial wilt. Management: Inspect lower leaves first; remove infected leaves; avoid overhead irrigation (use drip); improve airflow between plants; remove plant debris after harvest; rotate with non-solanaceous crops every 2-3 years; use disease-resistant varieties; apply fungicide only after diagnosis confirmation.",
                suggestions=[
                    "Use drip irrigation for tomato fields",
                    "Ensure 2-3 feet spacing between plants",
                    "Remove lower leaves weekly",
                    "Rotate with corn or bean crops",
                ],
            ),
            KnowledgeItem(
                question="Rice blast disease identification and control",
                answer="Rice blast appears as spindle-shaped brown spots on leaves with gray centers. Control measures: Use resistant varieties; maintain proper water management (avoid flooding/drying cycles); apply balanced fertilizer (avoid excess nitrogen); drain field before heading stage; use approved fungicides if disease pressure is high; clean equipment between fields; destroy infected plant debris.",
                suggestions=[
                    "Choose blast-resistant rice varieties",
                    "Maintain consistent water levels",
                    "Scout fields at tillering and heading",
                    "Report to agricultural extension office",
                ],
            ),

            # Pest Management
            KnowledgeItem(
                question="How can I control pests without excessive chemicals?",
                answer="Integrated Pest Management (IPM): Install pheromone traps for early pest detection; scout fields every 2-3 days; use sticky traps for monitoring; implement cultural control (crop rotation, field sanitation); plant trap crops; use biological control (beneficial insects); apply pesticides only when pest population exceeds economic threshold; spray during evening hours; use targeted sprays rather than blanket applications.",
                suggestions=[
                    "Install pheromone traps at field entry",
                    "Scout fields twice weekly",
                    "Use biological control agents",
                    "Apply neem or other organic options first",
                ],
            ),
            KnowledgeItem(
                question="Armyworm and bollworm pest control strategies",
                answer="Armyworms and bollworms damage leaves and fruiting bodies. Detection: Look for irregular leaf feeding patterns and frass (pest droppings). Control: Scout every 2-3 days; use pheromone traps for timing; apply Bt (Bacillus thuringiensis) spray at egg-laying stage; install light traps at night; maintain field sanitation; use resistant varieties; apply targeted pesticides only when threshold exceeded.",
                suggestions=[
                    "Install 5-6 pheromone traps per acre",
                    "Apply Bt spray at first sign",
                    "Light traps for night monitoring",
                    "Remove third crop if infestation severe",
                ],
            ),

            # Irrigation Management
            KnowledgeItem(
                question="Best irrigation strategy for hot and dry weather",
                answer="During hot weather: Irrigate early morning (5-8 AM) to reduce evaporation; apply deep irrigation to 30-45 cm depth; add 5-8 cm mulch layer to reduce water loss; avoid midday watering; check soil moisture at 10-15 cm depth; increase irrigation frequency during critical growth stages (flowering, fruit development); consider drip irrigation for 25-40% water savings; schedule irrigation every 5-7 days rather than frequent shallow watering.",
                suggestions=[
                    "Increase mulch thickness gradually",
                    "Install soil moisture sensors",
                    "Switch to drip irrigation permanently",
                    "Track irrigation amounts and dates",
                ],
            ),
            KnowledgeItem(
                question="Rice irrigation management and water saving tips",
                answer="Rice irrigation requires 1000-1500 mm water total. Best practices: Maintain 5 cm standing water during main season; use intermittent flooding (flood-drain-flood) to save 20-30% water; drain field 20-30 days before harvest; avoid flooding adjacent fields simultaneously; use raised beds with zero-tillage; repair field bunds to prevent seepage; use water-efficient rice varieties.",
                suggestions=[
                    "Implement alternate wetting and drying",
                    "Repair field bunds before season",
                    "Use certified water-efficient varieties",
                    "Install water measurement devices",
                ],
            ),

            # Nutrient Management & Fertilizer
            KnowledgeItem(
                question="Complete fertilizer schedule guide for major crops",
                answer="Fertilizer must match crop stage: Basal application before sowing (phosphorus, potassium, micronutrients); split nitrogen into 2-3 doses at tillering and heading stages; apply foliar nutrients during stress periods. Recommend soil testing first. Typical NPK for: Rice (120:60:60), Wheat (100:60:40), Cotton (150:75:50). Apply half basal dose + half top dressing. Organic sources: Neem cake, seaweed extract for micronutrients, vermicompost. Monitor for deficiency symptoms and correct immediately.",
                suggestions=[
                    "Conduct soil test before fertilizer plan",
                    "Apply urea in split doses",
                    "Use micronutrient chelates if deficient",
                    "Consider organic fertilizer options",
                ],
            ),
            KnowledgeItem(
                question="Micronutrient deficiency symptoms and correction",
                answer="Zinc deficiency: Brown spots on new leaves, stunted growth. Add zinc sulfate 10 kg/acre. Iron deficiency: Yellowing between leaf veins, pale new leaves. Add iron sulfate 5 kg/acre. Boron deficiency: Thick, brittle stems, dark discoloration. Add borax 1-2 kg/acre. Magnesium: Yellowing between veins on older leaves. Add Epsom salt foliar spray. Copper: Wilting tips, bleached patches. Use copper sulfate spray. Apply all foliar sprays during evening hours.",
                suggestions=[
                    "Observe leaf symptoms carefully",
                    "Get soil test done before correction",
                    "Apply foliar sprays in evening",
                    "Repeat spray if no improvement in 2 weeks",
                ],
            ),

            # Market & Price Management
            KnowledgeItem(
                question="When and how to sell crops for best market price",
                answer="Market timing strategy: Track price trends for 5-7 days minimum; compare at least 3 nearby mandis; calculate transport cost and mandi charges (typically 2-3% commission); compute net price received; avoid single-day panic selling after harvest; sell in small lots if prices are volatile; store quality produce for 1-2 weeks if prices are falling; sell directly to processors during peak supply if possible. Quality grading improves price by 5-10%.",
                suggestions=[
                    "Compare at least 3 mandi prices daily",
                    "Calculate all costs before deciding",
                    "Use quality-based grading method",
                    "Consider direct buyer contacts",
                ],
            ),
            KnowledgeItem(
                question="Post-harvest handling and storage practices",
                answer="Post-harvest management directly affects price. Best practices: Harvest at maturity stage (not overripe/underripe); harvest in early morning; handle carefully to avoid bruising; grade and sort by size/quality immediately; store at proper temperature and humidity (varies by crop); use ventilated storage for grains (8-12% moisture); prevent pest access to storage; maintain cleanliness; inspect stored produce every 2-3 days; use natural pest deterrents (dried neem leaves, turmeric powder).",
                suggestions=[
                    "Build storage with proper ventilation",
                    "Check moisture content before storage",
                    "Inspect stored produce regularly",
                    "Use quality containers for transport",
                ],
            ),

            # Soil & Crop Rotation
            KnowledgeItem(
                question="Soil preparation and pre-sowing checklist",
                answer="Proper soil preparation ensures better germination and yield. Steps: Conduct soil test 4-6 weeks before sowing; add recommended lime/sulfur if pH incorrect; plow 2-3 times and harrrow 3-4 times to break hardpan; remove weeds and stubble; add 5-10 tons organic matter (compost/FYM) per acre; let soil settle for 1-2 weeks; create proper field bunding; install irrigation channels if needed; level field for uniform flooding/drainage.",
                suggestions=[
                    "Conduct soil test immediately",
                    "Add organic matter 3-4 weeks early",
                    "Plow and harrow multiple times",
                    "Ensure proper field leveling",
                ],
            ),
            KnowledgeItem(
                question="Crop rotation benefits and planning strategy",
                answer="Crop rotation is essential for soil health and pest control. Benefits: Breaks pest/disease cycles; improves soil nitrogen (legumes); prevents nutrient mining; reduces chemical need. Good rotations: Cereal → Legume → Oilseed → Cereal for 3-year cycle. For 2-year: Cereal → Legume. Avoid consecutive crops from same family. Example: Rice → Pulses → Vegetables → Rice. Legumes (peas, beans, chickpea) add 40-60 kg nitrogen naturally. Track rotation plan and follow it strictly.",
                suggestions=[
                    "Plan rotation for 3-year cycle minimum",
                    "Include legumes in every rotation",
                    "Maintain rotation record",
                    "Choose crops based on market demand",
                ],
            ),

            # Weather-Based Farming
            KnowledgeItem(
                question="How to farm based on weather forecasts and seasonal patterns",
                answer="Use weather data for crop planning: Monitor 10-day and 30-day forecasts; adjust irrigation based on rainfall forecast; schedule sprayings before rain to avoid wash-off; avoid fertilizer application before heavy rain; plant after good rain for germination; delay harvest if heavy rain predicted (avoid grain damage). Key metrics: Track rainfall, temperature (min-max), humidity, wind speed. Adjust practices: High humidity → increase fungicide; below-normal rain → increase irrigation; above-normal temp → increase water management.",
                suggestions=[
                    "Check weather forecast daily",
                    "Adjust irrigation based on rainfall",
                    "Spray before predicted rain",
                    "Track local weather patterns yearly",
                ],
            ),

            # Yield Improvement
            KnowledgeItem(
                question="How to increase crop yield by 20-30 percent",
                answer="Yield increase requires integrated approach: Use certified quality seed of high-yielding varieties; ensure timely sowing at correct spacing (avoid crowding); maintain optimal plant population; apply balanced nutrition split by growth stages; scout for pests/diseases and control early; maintain proper irrigation during critical stages (flowering, grain-filling); reduce weed competition; avoid waterlogging; harvest at proper maturity. Combined effect of these practices can increase yield by 25-35% compared to conventional farming.",
                suggestions=[
                    "Get field checklist for each crop",
                    "Check recommended plant spacing",
                    "Monitor critical growth stages",
                    "Harvest at proper maturity stage",
                ],
            ),

            # Original knowledge items (kept for compatibility)
            KnowledgeItem(
                question="How should I decide when to sell crops in market?",
                answer="Market decision requires analysis: Track price trends for 5-7 days; compare at least 3 nearby mandis; include transport, storage, and commission costs in calculation; sell in batches if prices volatile; avoid panic selling immediately after harvest; check quality before sale; consider direct buyer options. Price differences between mandis can be 10-15%, so research is important. Sell during non-peak hours for better negotiation.",
                suggestions=[
                    "Compare at least 3 nearby markets",
                    "Calculate net price carefully",
                    "Avoid spike-day panic selling",
                    "Grade produce before sale",
                ],
            ),
        ]

    def _build_large_corpus(self, external_dir: Optional[Path] = None) -> List[Dict[str, object]]:
        """Build larger local corpus from Planning files and curated expert snippets."""
        docs: List[Dict[str, object]] = []
        crop_names: List[str] = []

        for item in self.knowledge:
            docs.append({"text": f"{item.question}. {item.answer}", "suggestions": item.suggestions})

        planning_dir = self.base_dir / "Planning"
        if planning_dir.exists():
            for file_path in planning_dir.glob("*.txt"):
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    lines = [line.strip("\t•- ") for line in content.splitlines() if line.strip()]
                    crop_name = file_path.stem.replace("_", " ")
                    crop_names.append(crop_name)
                    chunk: List[str] = []
                    for line in lines:
                        chunk.append(line)
                        if len(chunk) >= 4:
                            docs.append({
                                "text": f"{crop_name} guide: " + " ".join(chunk),
                                "suggestions": [
                                    f"Best sowing time for {crop_name}?",
                                    f"Fertilizer plan for {crop_name}",
                                    f"Common diseases in {crop_name}",
                                ],
                            })
                            chunk = []
                    if chunk:
                        docs.append({
                            "text": f"{crop_name} guide: " + " ".join(chunk),
                            "suggestions": [
                                f"Best sowing time for {crop_name}?",
                                f"Irrigation plan for {crop_name}",
                                f"Harvest timing for {crop_name}",
                            ],
                        })
                except Exception as exc:
                    logger.warning("Could not load planning file %s: %s", file_path.name, exc)

        docs.extend(self._generate_synthetic_crop_docs(crop_names))

        ext_dir = external_dir or self.default_external_corpus_dir
        docs.extend(self._load_external_corpus_docs(ext_dir))

        return docs

    def _load_external_corpus_docs(self, external_dir: Path) -> List[Dict[str, object]]:
        """Load additional corpus documents from CSV, JSON, JSONL, and TXT files."""
        if not external_dir.exists():
            return []

        docs: List[Dict[str, object]] = []
        for file_path in external_dir.rglob("*"):
            if not file_path.is_file():
                continue

            suffix = file_path.suffix.lower()
            try:
                if suffix == ".csv":
                    with file_path.open("r", encoding="utf-8", errors="ignore", newline="") as csv_file:
                        reader = csv.DictReader(csv_file)
                        for row in reader:
                            text = (row.get("text") or row.get("question") or row.get("answer") or "").strip()
                            suggestions_raw = (row.get("suggestions") or "").strip()
                            suggestions = [s.strip() for s in suggestions_raw.split("|") if s.strip()]
                            if text:
                                docs.append({"text": text, "suggestions": suggestions})

                elif suffix == ".jsonl":
                    with file_path.open("r", encoding="utf-8", errors="ignore") as jsonl_file:
                        for line in jsonl_file:
                            line = line.strip()
                            if not line:
                                continue
                            item = json.loads(line)
                            text = str(item.get("text") or item.get("question") or "").strip()
                            suggestions = item.get("suggestions") or []
                            if text:
                                docs.append({"text": text, "suggestions": list(suggestions)})

                elif suffix == ".json":
                    content = json.loads(file_path.read_text(encoding="utf-8", errors="ignore"))
                    if isinstance(content, dict):
                        content = [content]
                    if isinstance(content, list):
                        for item in content:
                            if not isinstance(item, dict):
                                continue
                            text = str(item.get("text") or item.get("question") or "").strip()
                            suggestions = item.get("suggestions") or []
                            if text:
                                docs.append({"text": text, "suggestions": list(suggestions)})

                elif suffix == ".txt":
                    raw = file_path.read_text(encoding="utf-8", errors="ignore")
                    blocks = [blk.strip() for blk in raw.split("\n\n") if blk.strip()]
                    for block in blocks:
                        docs.append({"text": block, "suggestions": []})
            except Exception as exc:
                logger.warning("Skipping malformed corpus file %s: %s", file_path, exc)

        if docs:
            logger.info("Loaded %s external corpus docs from %s", len(docs), external_dir)
        return docs

    def _generate_synthetic_crop_docs(self, crop_names: List[str]) -> List[Dict[str, object]]:
        """Generate large farmer-centric Q/A corpus for broader intent coverage and diverse responses."""
        if not crop_names:
            crop_names = [
                "Rice", "Cotton", "Maize", "Groundnut", "Soybean",
                "Sugarcane", "Turmeric", "Chilies", "Bajra", "Red Gram",
            ]

        # Enhanced templates with more detailed, clear responses
        templates = [
            (
                "Best sowing time and seed rate for {crop}",
                "For {crop}, optimal sowing window is region-specific - consult your local agricultural extension office. Prepare seedbed 2-3 weeks in advance. Use certified quality seed at recommended rate: {crop} requires 15-25 kg/acre. Avoid delayed sowing beyond the optimal window which reduces yield by 10-15%. Soak seeds in water for 4-6 hours before sowing. Space plants according to variety for better plant-to-plant competition.",
                ["Check soil prep for {crop}", "Ask seed treatment steps", "Get spacing recommendation for {crop}"],
            ),
            (
                "Complete fertilizer application schedule for {crop}",
                "Fertilize {crop} in stages for best results: Before sowing - apply phosphorus (P) and potassium (K) based on soil test. At tillering (25-30 days) - apply 50% nitrogen (N). At shooting (50-60 days) - apply remaining 50% N. At flowering - apply micronutrients if deficiency symptoms visible. Conduct soil test before planning. Split application increases nutrient efficiency by 20-30%. Use organic matter for 50% nutrient requirement if possible.",
                ["Get soil test details for {crop}", "Ask micronutrient plan", "Check organic alternatives for {crop}"],
            ),
            (
                "Major disease identification and management for {crop}",
                "Common {crop} diseases include fungal infections (spots, blights), bacterial infections (wilt, leaf scorch), and viral infections (leaf mottling, stunting). Identify by: observed symptoms, symptom location, timing of appearance. Prevent: use resistant varieties, crop rotation, proper spacing, avoid overhead water. Treat: remove affected plant parts, use approved fungicides/bactericides only after diagnosis. Monitor fields every 3-4 days for early detection.",
                ["Ask symptoms of major {crop} diseases", "Get {crop} disease prevention checklist", "Connect to AI Diagnosis for leaf images"],
            ),
            (
                "Pest population scouting and control threshold for {crop}",
                "Scout {crop} fields every 2-3 days for pest presence. Common pests: leaf-feeding insects, fruit-boring insects, sap-sucking insects. Set economic threshold (pest count at which treatment becomes profitable): usually 5-10% leaf damage or 1-2 insects per plant. Control methods in order: field sanitation, pheromone traps, biological control, targeted pesticides. Apply pesticides only when threshold exceeded to reduce chemical use and cost.",
                ["Ask economic threshold for {crop}", "Get integrated pest management steps", "Ask recommended pesticides if needed"],
            ),
            (
                "Stage-wise irrigation schedule and water management for {crop}",
                "Irrigate {crop} based on crop stage and soil moisture: Critical water requirement stages are germination, tillering, flowering, and grain-fill. Check moisture at 15 cm depth - if soil crumbles, irrigate. Total water needed: 800-1200 mm depending on climate. During rainy season: reduce irrigation frequency. In summer: increase to every 5-7 days. Use mulch (5-8 cm) to conserve moisture. Drip irrigation saves 25-40% water compared to flood irrigation.",
                ["Ask {crop} irrigation at each growth stage", "Get water-saving techniques", "Check rainy season irrigation adjustments"],
            ),
            (
                "How to increase {crop} yield by 25-30 percent",
                "Multi-factor yield improvement approach: Use certified high-yield variety seed (15-25% yield advantage). Optimize plant population (use correct spacing - consult variety guide). Apply balanced nutrition split by growth stage (5-10% yield increase). Scout and control pests/diseases early (prevents 10-15% yield loss). Maintain proper irrigation (15-20% improvement). Harvest at correct maturity stage. These combined practices can increase yield by 25-35% compared to conventional farming.",
                ["Get {crop} variety recommendation for your region", "Ask critical growth stage monitoring", "Check harvest maturity indicators"],
            ),
            (
                "Post-harvest handling and storage for {crop}",
                "Proper post-harvest handling increases price realization by 5-20%. Steps: Harvest at correct maturity stage (overripe/underripe reduces value). Harvest during cool early morning hours. Handle produce gently to avoid bruising. Grade and sort by size/quality immediately. Store at proper temperature and humidity for {crop}. Use ventilated storage with air circulation. Maintain 8-12% moisture for grains. Prevent pest access using screens and natural deterrents. Inspect stored produce every 3-5 days.",
                ["Ask {crop} harvest indicators", "Check optimal storage conditions", "Get grading and sorting tips"],
            ),
            (
                "Market price tracking and selling strategy for {crop}",
                "For {crop}, monitor mandi prices for minimum 3-5 days before selling. Compare at least 3 nearby mandis - price differences can be 10-15%. Calculate actual net price received (subtract transport 2-5%, mandi charges 2-3%, other costs). Sell in small lots if prices volatile. Time sales during off-peak hours for better negotiation. Quality grading can increase price by 8-12%. Direct buyer sales often better than mandi sales.",
                ["Check current {crop} market prices", "Compare nearby mandis", "Get quality grading tips for {crop}"],
            ),
            (
                "Soil preparation before {crop} sowing",
                "Prepare soil properly for better establishment: Conduct soil pH test - ideal range 6.0-7.0 for {crop}. Plow field 2-3 times breaking soil to 20-25 cm depth. Harrow 3-4 times to achieve fine tilth. Add 5-10 tons compost/FYM per acre (increases organic matter, water retention). Remove previous crop debris and weeds completely. Create proper field bunds/channels for water management. Let prepared soil settle 1-2 weeks before sowing. Improve soil structure for better root penetration.",
                ["Get soil test recommendations", "Ask organic matter addition rates", "Check field preparation timeline"],
            ),
            (
                "Crop rotation planning and benefits for {crop}",
                "Crop rotation improves soil health and reduces pest/disease buildup: Avoid planting {crop} or related crops in same field more than 1 year in 3-year cycle. Follow rotation: Cereal → Legume → Oilseed → Cereal. Legumes (peas, chickpea) add 40-60 kg nitrogen naturally. Each crop type depletes different soil nutrients - rotation prevents mining. Maintain written rotation record for future planning. Rotation reduces pest/disease pressure reducing chemical requirement.",
                ["Suggest crop rotation for my farm", "Ask benefits of rotating with legumes", "Get 3-year rotation plan"],
            ),
        ]

        generated: List[Dict[str, object]] = []
        
        # Generate base templates for each crop
        for crop in crop_names:
            for question_template, answer_template, suggestion_templates in templates:
                generated.append(
                    {
                        "text": f"{question_template.format(crop=crop)}. {answer_template.format(crop=crop)}",
                        "suggestions": [s.format(crop=crop) for s in suggestion_templates],
                    }
                )

        # Add season and weather-based advisories
        seasons_data = {
            "kharif": {"risks": ["early cessation of rain", "waterlogging", "fungal diseases"], "irrigation": "reduced", "focus": "manage excess water"},
            "rabi": {"risks": ["frost risk", "dry spells", "fungal infections"], "irrigation": "supplemental", "focus": "cold protection"},
            "summer": {"risks": ["heat stress", "high evaporation", "water scarcity"], "irrigation": "frequent", "focus": "water conservation"},
        }
        
        for crop in crop_names:
            for season, season_info in seasons_data.items():
                for risk in season_info["risks"]:
                    generated.append(
                        {
                            "text": (
                                f"{crop} {season} season advisory: Manage {risk}. "
                                f"Monitor field every 2-3 days. Adjust {season_info['irrigation']} irrigation as needed. "
                                f"Plan preventive steps ahead. Key focus: {season_info['focus']}. "
                                f"Track weather forecast for timely crop management decisions."
                            ),
                            "suggestions": [
                                f"Get {crop} {season} fertilizer plan",
                                f"Ask {crop} {season} disease prevention",
                                f"Check {crop} market status in {season}",
                                f"Get {risk} management steps for {crop}",
                            ],
                        }
                    )

        # Add weather-based agriculture tips
        weather_scenarios = [
            ("Excess rainfall", "Ensure field drainage, apply fungicides, delay nitrogen application, improve airflow to plants"),
            ("Heat wave", "Increase irrigation frequency, apply mulch, avoid midday operations, increase spacing if possible"),
            ("Frost risk", "Use frost-tolerant varieties, avoid low-lying areas, do not apply nitrogen in frost season, protect with mulch"),
            ("Dry spell", "Deep irrigation, mulch thickly, use water-efficient varieties, reduce plant population slightly"),
        ]
        
        for scenario, advice in weather_scenarios:
            for crop in crop_names[:5]:  # Add for major crops to avoid explosion
                generated.append({
                    "text": f"Managing {crop} during {scenario.lower()}. {advice}. Monitor soil moisture closely. Adjust irrigation and nutrient schedule. Take immediate action if stress symptoms visible.",
                    "suggestions": [
                        f"How to save {crop} from {scenario.lower()}",
                        f"Emergency management for {crop}",
                        f"Recovery plan for affected {crop}",
                    ]
                })

        return generated

    def _detect_language(self, text: str) -> str:
        if not self.detect:
            return "en"
        if len(text.strip()) <= 3:
            return "en"
        try:
            detected = self.detect(text)
            return detected if detected in SUPPORTED_RESPONSE_LANGUAGES else "en"
        except Exception:
            return "en"

    def _translate_to_english(self, text: str, source_lang: str) -> str:
        if source_lang == "en" or not self.query_translator:
            return text
        try:
            return self.query_translator(source=source_lang, target="en").translate(text)
        except Exception:
            return text

    def _translate_from_english(self, text: str, target_lang: str) -> str:
        if target_lang == "en" or not self.answer_translator:
            return text
        try:
            return self.answer_translator(source="en", target=target_lang).translate(text)
        except Exception:
            return text

    def _get_tokens(self, text: str) -> List[str]:
        lowered = text.lower()
        if self.word_tokenizer and self.stemmer:
            tokens = self.word_tokenizer(lowered, r"[a-zA-Z]+")
            return [self.stemmer.stem(token) for token in tokens]
        return lowered.split()

    def _classify_intent(self, english_query: str) -> str:
        labels = [
            "greeting",
            "disease management",
            "pest control",
            "irrigation",
            "fertilizer planning",
            "market pricing",
            "weather advisory",
            "sowing and planting",
            "harvesting and yield",
            "soil and nutrients",
            "weed management",
            "crop rotation",
            "general farming",
        ]

        token_set = set(self._get_tokens(english_query))
        quick_map = {
            "greeting": {"hello", "hi", "hey", "namaste"},
            "disease management": {"diseas", "blight", "fungal", "viral", "bacteri", "spot", "wilt"},
            "pest control": {"pest", "insect", "worm", "aphid", "bollworm", "trap"},
            "irrigation": {"irrig", "water", "moistur", "drip", "flood"},
            "fertilizer planning": {"fertil", "npk", "nutrient", "manur", "urea"},
            "market pricing": {"market", "price", "sell", "mandi", "rate"},
            "weather advisory": {"weather", "rain", "humid", "temperatur", "wind"},
            "sowing and planting": {"sow", "seed", "plant", "nurseri", "transplant"},
            "harvesting and yield": {"harvest", "yield", "product", "flower"},
            "soil and nutrients": {"soil", "ph", "micronutri", "compost"},
            "weed management": {"weed", "herbicid"},
            "crop rotation": {"rotat", "intercrop", "legum"},
        }

        for intent, words in quick_map.items():
            if words.intersection(token_set):
                return intent

        if self.intent_classifier and len(english_query.split()) >= 5:
            try:
                result = self.intent_classifier(english_query, labels)
                return str(result["labels"][0])
            except Exception:
                pass

        return "general farming"

    def _intent_answer(self, intent: str, english_query: str) -> Dict[str, object]:
        query_lower = english_query.lower()

        if intent == "greeting":
            return {
                "answer": "Hello! I am your Farmer Assistant. Ask me crop-specific questions on disease, irrigation, fertilizer, market timing, and yield improvement.",
                "suggestions": [
                    "Tomato disease treatment",
                    "Best sowing time for rice",
                    "How to improve cotton yield",
                ],
                "confidence": 0.74,
            }

        if "tomato" in query_lower and ("disease" in query_lower or "blight" in query_lower or "spot" in query_lower):
            return {
                "answer": "For tomato disease management: identify symptom type (spots, wilt, curl), remove infected leaves, improve airflow, avoid overhead watering, and apply targeted control after likely diagnosis.",
                "suggestions": [
                    "Upload tomato leaf image in AI Diagnosis",
                    "Ask bacterial vs fungal symptom differences",
                    "Get preventive spray timing",
                ],
                "confidence": 0.83,
            }

        intent_templates = {
            "disease management": (
                "Disease control is most effective with early scouting, clean field hygiene, and targeted treatment. Confirm symptom pattern before spraying.",
                ["Inspect lower leaves first", "Separate infected plants", "Use threshold-based treatment"],
            ),
            "pest control": (
                "Use integrated pest management with traps, biological controls, and selective spraying only above threshold levels.",
                ["Install pheromone traps", "Scout every 2-3 days", "Spray at evening hours"],
            ),
            "irrigation": (
                "Irrigation should follow root-zone moisture and crop stage. Prefer early-morning irrigation during heat and conserve moisture with mulch.",
                ["Check soil at 10-15 cm depth", "Use drip if possible", "Split watering in sandy soil"],
            ),
            "fertilizer planning": (
                "Apply fertilizer in split stages using soil-test guidance. Balanced NPK and micronutrients improve yield and reduce stress.",
                ["Use soil test values", "Split nitrogen applications", "Add organic matter"],
            ),
            "market pricing": (
                "For better sale decisions, compare 5-7 day trends, nearby markets, and logistics cost. Selling in batches lowers volatility risk.",
                ["Compare 3 local mandis", "Track weekly trend", "Grade produce before sale"],
            ),
            "weather advisory": (
                "Align farm operations with forecast: irrigation, spraying, and field activities should adjust to rain, humidity, and temperature.",
                ["Avoid spray before rain", "Irrigate early in hot weather", "Pause pruning during wet spells"],
            ),
            "sowing and planting": (
                "Sowing success depends on right season, healthy seed, proper spacing, and good field preparation.",
                ["Use recommended seed variety", "Confirm ideal planting window", "Maintain row and plant spacing"],
            ),
            "harvesting and yield": (
                "Harvest at physiological maturity for best quality and price. Timely harvest prevents losses.",
                ["Check maturity indicators", "Avoid delayed harvest", "Dry produce to safe moisture"],
            ),
            "soil and nutrients": (
                "Healthy soil needs balanced nutrients, organic matter, and correct pH. Soil testing improves input efficiency.",
                ["Test soil before sowing", "Apply compost regularly", "Correct micronutrient deficiency early"],
            ),
            "weed management": (
                "Weed pressure should be controlled in early crop stage using integrated methods: mulching, timely weeding, and selective herbicides.",
                ["Control weeds in first 30 days", "Use pre-emergence where suitable", "Combine manual + chemical control"],
            ),
            "crop rotation": (
                "Crop rotation reduces pests and improves soil fertility. Alternate heavy feeders with legumes.",
                ["Rotate with pulse crops", "Avoid same family repeatedly", "Plan seasonal rotation map"],
            ),
        }

        if intent in intent_templates:
            answer_text, suggestion_list = intent_templates[intent]
            return {"answer": answer_text, "suggestions": suggestion_list, "confidence": 0.66}

        return {
            "answer": "I can help with disease, irrigation, fertilizer, weather, market decisions, sowing, harvesting, and crop planning. Ask a crop-specific question for a precise recommendation.",
            "suggestions": [
                "Best sowing time for cotton",
                "How to control leaf blight",
                "Fertilizer plan for rice",
            ],
            "confidence": 0.45,
        }

    def _dynamic_market_hint(self, region: str = "india") -> Optional[str]:
        try:
            prices = get_market_prices(region=region)
            if not prices:
                return None
            top = max(
                prices,
                key=lambda p: abs(float(str(p.get("change", "0")).replace("%", "").replace("+", "").replace("-", ""))),
            )
            return f"Latest market signal: {top['crop']} at {top['market']} is showing {top['change']} change today."
        except Exception:
            return None

    def _dynamic_weather_hint(self, city: Optional[str]) -> Optional[str]:
        if not city:
            return None
        try:
            weather = get_weather_data(city)
            if not weather:
                return None
            tips = generate_weather_advice(weather)
            if not tips:
                return None
            return (
                f"Weather in {weather.get('city', city)}: {weather.get('temperature', '--')}°C, "
                f"{weather.get('description', weather.get('condition', 'current conditions'))}. "
                f"Tip: {tips[0]}"
            )
        except Exception:
            return None

    def _retrieve_from_large_corpus(self, english_query: str) -> Dict[str, object]:
        if not (self.vectorizer and self.cosine_similarity and self.corpus_matrix is not None and self.corpus_docs):
            return {"answer": "", "suggestions": [], "confidence": 0.0}

        try:
            query_vector = self.vectorizer.transform([english_query])
            sims = self.cosine_similarity(query_vector, self.corpus_matrix)[0]
            top_idx = int(sims.argmax())
            score = float(sims[top_idx])
            if score < 0.15:
                return {"answer": "", "suggestions": [], "confidence": score}

            doc = self.corpus_docs[top_idx]
            return {
                "answer": str(doc["text"]),
                "suggestions": list(doc.get("suggestions", [])),
                "confidence": min(0.8, score + 0.2),
            }
        except Exception:
            return {"answer": "", "suggestions": [], "confidence": 0.0}

    def _retrieve_from_embeddings(self, english_query: str) -> Dict[str, object]:
        if not (self.model and self.util and self.knowledge_embeddings is not None):
            return {"answer": "", "suggestions": [], "confidence": 0.0}

        query_embedding = self.model.encode(english_query, convert_to_tensor=True)
        scores = self.util.cos_sim(query_embedding, self.knowledge_embeddings)[0]
        top_idx = int(scores.argmax())
        confidence = float(scores[top_idx])
        if confidence < 0.35:
            return {"answer": "", "suggestions": [], "confidence": confidence}

        best_item = self.knowledge[top_idx]
        return {
            "answer": best_item.answer,
            "suggestions": best_item.suggestions,
            "confidence": confidence,
        }

    def _get_cached(self, key: str) -> Optional[Dict[str, object]]:
        return self.response_cache.get(key)

    def _set_cache(self, key: str, value: Dict[str, object]) -> None:
        if len(self.response_cache) >= 500:
            self.response_cache.pop(next(iter(self.response_cache)))
        self.response_cache[key] = value

    def get_response(
        self,
        message: str,
        user=None,
        market_region: str = "india",
        response_language: str = "en",
    ) -> Dict[str, object]:
        preferred_lang = response_language if response_language in SUPPORTED_RESPONSE_LANGUAGES else "en"

        # English is default unless user selects another response language explicitly.
        source_lang = self._detect_language(message)
        english_query = self._translate_to_english(message, source_lang) if source_lang != "en" else message

        cache_key = f"{english_query.strip().lower()}::{market_region}::{preferred_lang}::{getattr(user, 'city', '')}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        intent = self._classify_intent(english_query)
        intent_result = self._intent_answer(intent, english_query)
        corpus_result = self._retrieve_from_large_corpus(english_query)
        embedding_result = self._retrieve_from_embeddings(english_query)

        answer = str(intent_result["answer"])
        suggestions = list(intent_result["suggestions"])
        confidence = float(intent_result["confidence"])

        for candidate in [corpus_result, embedding_result]:
            if candidate["answer"] and float(candidate["confidence"]) > confidence:
                answer = str(candidate["answer"])
                suggestions = list(candidate["suggestions"])
                confidence = float(candidate["confidence"])

        weather_hint = self._dynamic_weather_hint(getattr(user, "city", None))
        market_hint = self._dynamic_market_hint(region=market_region)
        dynamic_notes = [hint for hint in [weather_hint, market_hint] if hint]
        if dynamic_notes:
            answer = f"{answer}\n\n" + "\n".join(dynamic_notes)

        translated_answer = self._translate_from_english(answer, preferred_lang)

        result = {
            "answer": translated_answer,
            "language": preferred_lang,
            "confidence": round(confidence, 3),
            "intent": intent,
            "suggestions": suggestions,
            "model": PRETRAINED_MODEL_NAME if self.model else "keyword-fallback",
            "intent_model": INTENT_MODEL_NAME if self.intent_classifier else "keyword-intent-fallback",
            "corpus_size": len(self.corpus_docs),
        }
        self._set_cache(cache_key, result)
        return result
