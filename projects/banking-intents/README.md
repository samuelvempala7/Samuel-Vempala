# When should a banking support router ask for help?

“Where is my transfer?” could mean the transfer is pending, failed, or has cleared without reaching the recipient. This project uses the distance between the model’s top two intent scores to decide when to defer a query to a person.

On the cleaned BANKING77 test set, it automatically routed **2,885 of 3,051** questions. **2,623** of those routes matched the benchmark label. That leaves **262 wrong routes** and **166 questions deferred**. Routing every question gave 88.0% accuracy. Applying the handoff rule gave 90.9% accuracy on the routed subset at 94.6% coverage.

### A closer look at the misses

Six accepted questions about a cash withdrawal at an unexpected exchange rate went to the card-payment exchange-rate queue. Five questions about being *unable* to verify identity went to the general identity-verification queue. A reasonable next test would ask a clarifying question for these specific pairs and count the additional handoffs and corrected routes.

Training used word unigrams and bigrams, TF–IDF weights, and a linear support-vector classifier. I split the published training set into 7,977 fitting and 1,995 validation examples. I chose the smallest score margin on a fixed grid that cleared 90% validation accuracy on at least 100 routed cases. The winning margin was 0.10. The published test set stayed separate. Normalized exact duplicates were removed within splits and test matches to training were excluded. Paraphrases can still overlap. The test covers 77 known intents, so unrelated requests would need their own evaluation.

[Classifier and threshold selection](analyze.py) · [All accepted errors by intent pair](accepted_misroutes.csv) · [Evaluation counts](evaluation.csv) · [Reproduction instructions](../../RUNNING.md)

Dataset by Iñigo Casanueva and colleagues (2020), released under CC BY 4.0. [BANKING77 data and citation](https://github.com/PolyAI-LDN/task-specific-datasets/tree/master/banking_data)
