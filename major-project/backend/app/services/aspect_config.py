"""All tunable knowledge for aspect extraction lives in this one file.
A sentence's score for an aspect is a mix of three signals:
  1. embedding  - how close its meaning is to example sentences (PROTOTYPES)
  2. cue        - does it contain telltale phrases (CUES)
  3. position   - where in the paper it sits (POSITION), plus a small bonus
                  if the nearest heading matches (HEADING_HINTS)
Headings are only a hint: a paper with no 'Limitations' heading still works."""
import re

ASPECTS = ["problem", "objective", "methodology", "dataset",
           "results", "limitations", "future_work"]
GAP_ASPECTS = ["limitations", "future_work"]       # used for gap discovery
DESCRIPTIVE = [a for a in ASPECTS if a not in GAP_ASPECTS]

WEIGHTS = {"embedding": 0.4, "cue": 0.4, "position": 0.2}

# Limitation / future-work sentences MUST contain at least one real telltale
# phrase (cue score >= this). Stops generic sentences that merely "sound"
# similar (e.g. textbook definitions) from being picked.
GAP_MIN_CUE = 0.3

# Sentences in these sections mostly describe OTHER people's work, so their
# limitation/future-work score is reduced. Headings are only a soft hint.
RELATED_HEADINGS = {"related work", "related works", "literature review",
                    "background", "introduction", "abstract"}
RELATED_PENALTY = 0.5
CITATION_PENALTY = 0.6      # sentence cites another paper: "[12]" or "et al."

# Minimum final score to accept a sentence. TUNE THESE after testing.
THRESHOLD = {"problem": 0.45, "objective": 0.45, "methodology": 0.45,
             "dataset": 0.45, "results": 0.45, "limitations": 0.38,
             "future_work": 0.38}

# Every paper has a problem, objective, method, dataset and results, so for
# these we always show the best-ranked sentences (above this tiny floor).
# Only limitations / future work use THRESHOLD, because a paper may truly lack them.
MIN_DESCRIPTIVE_SCORE = 0.2

# Stage 3 (cross-paper comparison, like with like: dataset vs dataset, ...)
# How many statements per aspect each paper contributes to the comparison.
COMPARE_TOP_K = {"problem": 5, "objective": 4, "methodology": 8, "dataset": 6,
                 "results": 6, "limitations": 25, "future_work": 25}
MIN_PAIR_SIMILARITY = 0.30   # pairs below this are never sent to the browser
MAX_PAIRS = 60               # per aspect

# Closing remarks such as "Overall, our study highlights the potential of..."
# mention "the future" but are not real limitations / future work.
GAP_NEGATIVE = re.compile(
    r"^(overall|in summary|in conclusion|to sum up)\b|"
    r"\b(highlights?|underscores?|demonstrates?|showcases?) the "
    r"(potential|effectiveness|efficacy|robustness)\b", re.I)
GAP_NEGATIVE_PENALTY = 0.6
# Boilerplate that says nothing specific ("every study has limitations").
GAP_FILLER = re.compile(r"every (research|study|work|paper)\b.{0,25}\blimitations|not an exception", re.I)

# Default slider position per aspect = typical (baseline) similarity + margin
DEFAULT_THRESHOLD_MIN = 0.5
DEFAULT_THRESHOLD_MARGIN = 0.2

# Stage 4 (grouping statements into recurring issues)
# Limitations AND future work are pooled: what one paper lists as a limitation
# another often lists as future work ("small dataset" vs "needs more data").
CLUSTER_ASPECTS = ["limitations", "future_work"]
CLUSTER_MARGIN = 0.2          # default strictness = typical similarity + margin
CLUSTER_MIN, CLUSTER_MAX = 0.5, 0.85
# Evidence strength of a recurring issue (n = supporting papers, N = uploaded)
STRENGTH_HIGH = (3, 0.6)      # at least 3 papers AND 60% of the papers
STRENGTH_MEDIUM = (2, 0.4)    # at least 2 papers AND 40% of the papers

# Stage 5 (potential research gaps + evidence verification)
GAP_SUPPORT_MIN = 0.45        # gap wording must be this similar (on average) to its evidence
GAP_LLM_MAX_STATEMENTS = 8    # statements sent to the optional LLM
GAP_TITLE_MAX_CHARS = 140

# How many sentences to show per aspect
TOP_K = {"problem": 2, "objective": 2, "methodology": 3, "dataset": 3,
         "results": 3, "limitations": 6, "future_work": 6}

# (start, end) of the paper (0 = first sentence, 1 = last) where the aspect
# usually appears. Inside the window -> 1.0, outside -> 0.35.
POSITION = {"problem": (0, 0.3), "objective": (0, 0.3),
            "methodology": (0.1, 0.7), "dataset": (0.1, 0.7),
            "results": (0.35, 1.0), "limitations": (0.5, 1.0),
            "future_work": (0.65, 1.0)}

HEADING_HINTS = {
    "problem": ["abstract", "introduction", "background"],
    "objective": ["abstract", "introduction"],
    "methodology": ["method", "methods", "methodology", "proposed method",
                    "proposed methodology", "approach", "materials and methods"],
    "dataset": ["dataset", "datasets", "dataset description", "data collection",
                "experimental setup", "materials and methods"],
    "results": ["results", "experimental results", "results and discussion",
                "experiments and results", "experiments"],
    "limitations": ["limitations", "discussion", "results and discussion",
                    "conclusion", "conclusions", "limitations and future work",
                    "discussion and conclusion"],
    "future_work": ["future work", "future directions", "future research",
                    "conclusion", "conclusions", "conclusion and future work",
                    "limitations and future work"],
}

# Example sentences describing each aspect (compared by meaning).
PROTOTYPES = {
    "problem": [
        "Despite recent progress, this problem remains challenging and existing approaches fall short.",
        "Existing methods suffer from important drawbacks, which motivates the need for a better solution.",
        "The growing importance of this task creates a need for accurate and reliable automated methods.",
    ],
    "objective": [
        "In this paper, we propose a novel approach to address this problem.",
        "The aim of this work is to develop and evaluate a method for the task.",
        "We present a framework and investigate whether it improves performance.",
    ],
    "methodology": [
        "We train a deep neural network using the proposed architecture and an optimizer with a fixed learning rate.",
        "The proposed pipeline consists of preprocessing, feature extraction and classification stages.",
        "Our method applies an encoder followed by a classification layer.",
    ],
    "dataset": [
        "We evaluate our approach on a publicly available benchmark dataset containing thousands of labelled samples.",
        "The data was collected, annotated and split into training, validation and test sets.",
        "The dataset consists of samples gathered from several sources.",
    ],
    "results": [
        "Our method achieves higher accuracy and F1 score than the baseline methods.",
        "Experimental results show that the proposed approach outperforms state-of-the-art models.",
        "The model reaches 95% accuracy on the test set.",
    ],
    "limitations": [
        "A limitation of this study is that the dataset is small and lacks diversity.",
        "The approach does not generalize well to other settings and was not evaluated on real-world data.",
        "However, our method is computationally expensive and fails in certain difficult cases.",
        "These results are limited by the small number of samples used.",
    ],
    "future_work": [
        "In future work, we plan to evaluate the approach on larger and more diverse datasets.",
        "Future research should investigate how the method can be extended to other domains.",
        "Further work is needed to address these open challenges.",
    ],
}

# Telltale phrases: (regex, weight). 1.0 = strong, 0.6 = medium, 0.3 = weak.
_CUES = {
    "problem": [
        (r"\b(problem|challenge|issue)s? (of|in|is|are)\b", 0.6),
        (r"\bremains? (a )?(challenging|difficult|open)", 0.8),
        (r"\b(existing|current|previous|traditional) (methods|approaches|work|studies|systems)\b", 0.4),
        (r"\bgrowing need\b", 0.9), (r"\bthere is a (growing )?need for\b", 0.8),
        (r"\b(poses?|is|are) (a )?(significant|major|serious|persistent|growing) (challenge|problem|threat|concern)", 0.9),
        (r"\bsuffer(s)? from\b", 0.7), (r"\bmotivat", 0.6), (r"\bgap\b", 0.5),
        (r"\bdifficult to\b", 0.5), (r"\bis (important|essential|crucial|critical)\b", 0.4),
    ],
    "objective": [
        (r"\b(this|our) (paper|work|study|research|article)\b.{0,50}\b(propose|present|introduce|aim|investigate|develop|focus|address|explore)", 1.0),
        (r"\bwe (propose|present|introduce|aim|develop|investigate|address|explore|focus)\b", 0.8),
        (r"\bthe (aim|goal|objective|purpose)s? of\b", 1.0), (r"\bour (objective|aim|goal)s? (in|of|is)\b", 1.0),
        (r"\bobjectives? (of|in) this\b", 1.0),
        (r"\bin this (paper|work|study)\b", 0.6), (r"\bour (contribution|goal|aim)", 0.8),
        (r"\bto (address|solve|tackle) (this|these|the)\b", 0.5),
    ],
    "methodology": [
        (r"\bwe (use|used|employ|employed|apply|applied|train|trained|implement|implemented|adopt|adopted|design|designed|extract|compute|fine-tune|fine-tuned|build|built|utili[sz]e)", 0.8),
        (r"\b(architecture|framework|pipeline|algorithm|neural network|module|layers?|backbone|loss function|optimi[sz]er|preprocessing|augmentation)\b", 0.5),
        (r"\bproposed (method|approach|model|framework|architecture)", 0.7),
        (r"\bconsist(s|ing)? of\b", 0.4), (r"\bhyperparameter", 0.6),
        (r"\b(were|was) (evaluated|applied|employed|used|trained|tested|implemented)\b", 0.6),
        (r"\b(KNN|SVM|SVC|random forest|decision trees?|logistic regression|naive bayes|xgboost|lightgbm|CNN|LSTM|RNN|ANN)\b", 0.4),
        (r"\bepochs?\b", 0.6), (r"\blearning rate", 0.7),
    ],
    "dataset": [
        (r"\bdata ?sets?\b", 0.8), (r"\bcorpus\b", 0.7), (r"\bbenchmark", 0.5),
        (r"\b(collected|annotated|labell?ed|curated)\b", 0.5),
        (r"\b\d[\d,]*\s+(images|samples|instances|documents|records|patients|papers|examples|sentences|articles)", 0.8),
        (r"\b(train(ing)?|validation|test)\s+(set|split|data)\b", 0.6),
        (r"\bpublicly available\b", 0.5),
    ],
    "results": [
        (r"\b(achiev|obtain|attain|reach|report)(s|ed|es|ing)?\b.{0,60}\b(accuracy|precision|recall|f1|f-score|auc|map|score|performance|error|rmse|bleu|rouge)", 1.0),
        (r"\boutperform", 0.9), (r"\b(accuracy|f1|precision|recall|map|auc)\b.{0,20}\d", 0.7),
        (r"\d+(\.\d+)?\s?%", 0.5), (r"\bcompared (to|with)\b", 0.4),
        (r"\bresults? (show|indicate|demonstrate|reveal|suggest)", 0.9),
        (r"\bimprov(e|es|ed|ement)\b.{0,30}\b(over|by)\b", 0.6),
        (r"\bstate-of-the-art\b", 0.4),
    ],
    "limitations": [
        (r"\blimitations?\b", 1.0), (r"\blimited (to|by|in)\b", 0.8),
        (r"\bdoes not (generali[sz]e|account|consider|handle|address|capture)", 0.9),
        (r"\b(unable|fail(s|ed)?) to\b", 0.8), (r"\bdrawbacks?\b", 0.9),
        (r"\bshortcomings?\b", 0.9), (r"\bweakness", 0.9), (r"\bcaveats?\b", 0.8),
        (r"\b(small|limited|insufficient|scarcity of|lack of)\b.{0,60}\b(data|datasets?|samples|diversity)", 0.9),
        (r"\blimits?\b", 0.7),
        (r"\bonly (been )?(tested|evaluated|validated|studied|applied)\b", 0.8),
        (r"\bcare should be (used|taken)\b", 0.7), (r"\bsmall number of\b", 0.5),
        (r"\brequires? (a lot of|large|significant|substantial) .{0,30}(resources|computation|data)", 0.7),
        (r"\bcomputational (complexity|resources|cost)\b", 0.5), (r"\btrade-?offs?\b", 0.5),
        (r"\bnot (been )?(evaluated|tested|validated|explored)\b", 0.8),
        (r"\bremains? (a )?(challenge|unclear|unresolved|unsolved)", 0.7),
        (r"\bcomputationally (expensive|costly|intensive)\b", 0.7),
        (r"\bstruggles?\b", 0.5), (r"\bbias(ed)?\b", 0.4), (r"\bhowever\b", 0.2),
    ],
    "future_work": [
        (r"\bfuture (work|research|studies|study|directions?)\b", 1.0),
        (r"\bin the future\b", 0.8), (r"\bwe (plan|intend|aim|hope) to\b", 0.8),
        (r"\bfurther (research|investigation|work|study|studies|exploration|experiments?)\b", 0.8),
        (r"\bshould (be )?(explored|investigated|evaluated|extended|addressed|considered|tested)", 0.8),
        (r"\b(could|can) be (extended|explored|improved|applied)\b", 0.6),
        (r"\bremains? to be\b", 0.7), (r"\bwill be (explored|investigated|addressed)\b", 0.8),
        (r"\bopen (problem|question|challenge)s?\b", 0.7), (r"\bpromising (direction|avenue)", 0.7),
        (r"\b(more )?(efforts|research|work|studies|investigation) (is|are) (needed|required)\b", 0.9),
        (r"\bneeds? to be (investigated|explored|addressed|studied|maintained)\b", 0.8),
        (r"\blooking ahead\b", 0.8),
    ],
}
COMPILED_CUES = {a: [(re.compile(p, re.IGNORECASE), w) for p, w in cues]
                 for a, cues in _CUES.items()}
