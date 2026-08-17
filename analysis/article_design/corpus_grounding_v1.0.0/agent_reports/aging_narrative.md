# Biological-aging narrative analysis of the exploratory 101-report corpus

## Executive conclusion

The corpus does not represent one biologically uniform field of "multi-omics aging." It contains at least four different scientific objects:

1. organismal longevity, survival, healthspan, and maintenance of function;
2. natural age-associated change in tissues, organs, and physiological response capacity;
3. cellular or tissue senescence in natural aging, acute injury, chronic disease, cancer, reproduction, and experimentally induced stress;
4. molecular or imaging proxies of biological age, including epigenetic, metabolomic, proteomic, and multi-organ age gaps.

These objects overlap, but they are not interchangeable. A clock shift is not a lifespan effect; stress-induced senescence in an acute disease model is not natural aging; delayed tumor-cell senescence can promote cancer even though senescent-cell accumulation can promote tissue aging; and post-ovulatory, placental, plant, and fruit senescence have distinct biological time scales and functions.

The most defensible biological storyline is therefore **multi-scale loss or restoration of biological resilience**, with explicit stratification by aging phenomenon, model, tissue, and the role aging plays in each analysis. Organismal survival and function should anchor the narrative. Natural tissue aging, senescence-centered pathology, age-related disease, and intervention response should follow. Biological-age clocks should be treated as measurement systems rather than as a synonym for aging or rejuvenation.

A broad standalone Results section called "aging mechanisms" would currently overstate coherence. The corpus supports a smaller final Results subsection on **recurrent biological response axes across evidence strata**, provided that it keeps effect-supported links separate from pathway interpretation and does not imply that every report instantiates a Hallmark of Aging.

This report is exploratory article-structure work only. It does not alter eligibility, PRISMA counts, report linkage, or causal levels.

## Scope and method

### Corpus-wide orientation

All 101 records in `eligible_graph_profiles_101.jsonl` were used. The manifest and `corpus_graph_summary.json` were checked for completeness and provenance. The graph pack contains 101 canonical graphs and 686 model-generated aging-construct candidates. Graph labels, `identification_status`, and causal-design labels were used only to orient the corpus and select full texts; they were not accepted as biological or causal ground truth.

At the report level, the graph profiles contain the following nonexclusive candidate signals:

| Candidate graph role | Reports with at least one candidate |
|---|---:|
| Aging outcome or trajectory | 94 |
| Aging mechanism | 86 |
| Aging intervention target | 49 |
| Longevity or healthspan | 48 |
| Age context only | 29 |
| Other aging-context label | 1 |

These are orientation counts, not review findings. In particular, a graph can label a pathway mention as a mechanism or a molecular reversal as rejuvenation without establishing either conclusion.

A deterministic text scan across titles and profile fields further found nonexclusive signals in 65 reports for cellular/tissue senescence, 53 for survival/lifespan/longevity/healthspan, 28 for induced or premature aging/stress-senescence models, 9 for reproductive or gestational constructs, 12 for cancer/tumor senescence contexts, and 5 for plant or fruit senescence/longevity. These counts are useful for defining strata, not for replacing claim-level extraction.

### Full-text verification

I inspected 40 distinct deterministic Docling Markdown reports selected to span the candidate phenomena, species, tissues, intervention types, and edge cases. Thirty-four had explicit Results and Discussion sections; the remainder were short-form articles, a preprint, a thesis, a publisher-preview structure, or used nonstandard section headings. Strong synthesis conclusions below rely on the substantive sectioned reports, with shorter reports used mainly to test boundaries.

Inspection focused on the abstract/summary, model and exposure definitions, relevant Results subsections, and Discussion interpretation. The checked reports are listed in the final audit section. This exceeds the requested minimum of 25 representative full texts.

## What aging phenomena the corpus covers

### 1. Organismal longevity and healthspan are real but not dominant endpoints

The corpus includes genuine survival experiments and functional aging outcomes across vertebrate and invertebrate systems.

- In **"Genetic perturbation of AMP biosynthesis extends lifespan and restores metabolic health in a naturally short-lived vertebrate"** (DOI `10.1016/j.devcel.2023.05.015`), Results subsection **"Male-specific lifespan extension in APRT D8/+ heterozygous fish"** reports about a 17% increase in median lifespan and about a 24% increase in the 90th-percentile lifespan in male killifish, but no female lifespan effect. Later Results sections connect the effect to age-dependent metabolic plasticity in liver and muscle. This is direct organismal aging evidence with sex specificity.
- In **"Multiomic profiling of the liver across diets and age in a diverse mouse population"** (DOI `10.1016/j.cels.2021.09.005`), **"Clinical analysis of lifespan as a function of genotype and diet"** analyzes natural-death lifespan in 1,336 female mice across 66 BXD strains and two diets. The paper then tests selected liver candidates in *C. elegans*. This is natural lifespan variation plus cross-species perturbation, not simply an aging-signature study.
- In **"Restoration of energy homeostasis by SIRT6 extends healthy lifespan"** (DOI `10.1038/s41467-021-23545-7`), the Results and Discussion combine lifespan extension in both sexes with maintained activity, reduced age-related pathology, and preserved liver/adipose energy handling. This is one of the clearest lifespan-plus-function anchors.
- In **"Reducing the metabolic burden of rRNA synthesis promotes healthy longevity in Caenorhabditis elegans"** (DOI `10.1038/s41467-024-46037-w`), **"Levels of pre-rRNA synthesis control lifespan and healthspan"** and **"Curbed ribosome biogenesis delays metabolic aging"** link survival, neuromuscular performance, intestinal integrity, ATP maintenance, and late-life intervention timing.
- In **"Multi-omic rejuvenation and lifespan extension upon exposure to youthful circulation"** (DOI `10.1038/s43587-023-00451-9`), **"Long-term parabiosis followed by detachment extends lifespan and healthspan in mice"** reports a six-week median-lifespan extension, physiological benefits, and persistent blood/liver epigenetic-age reduction. It is unusual because molecular rejuvenation, function, and survival are all measured.
- **"Targeted Bmal1 restoration in muscle prolongs lifespan with systemic health effects in aging model"** (DOI `10.1172/jci.insight.174007`) reports in Results that muscle-specific *Bmal1* restoration improves survival, mobility, glucose handling, and systemic inflammatory markers in a global *Bmal1*-knockout premature-aging model. It is an organismal intervention result, but in an induced short-lifespan model rather than natural aging.

The narrative should therefore include organismal longevity as a visible anchor, while distinguishing natural-death lifespan, genetically shortened lifespan, and proxy outcomes. "Healthspan" also needs operational detail: in different papers it means mobility, stress resistance, tissue integrity, metabolic flexibility, reduced pathology, or a composite GWAS phenotype.

### 2. Natural aging is often expressed as loss of tissue function or response capacity

Many reports compare young/adult and naturally aged organisms without measuring lifespan. Their common biological question is not "what makes an organism live longer?" but "what changes with age, and can an aged tissue still respond?"

- **"The Age-Dependent Resident Myonuclear Multi-Omic Response to an Acute Skeletal Muscle Hypertrophic Stimulus in Mice"** (DOI `10.1002/advs.202521633`) compares 6-8-month and 24-month mouse muscle. Results distinguish baseline age effects from age-by-mechanical-overload differences and identify compromised myonuclear plasticity. Aging is both a trajectory and an effect modifier of an acute response.
- **"Spatiotemporal mapping reveals Ccl8hi macrophages as key drivers of testicular inflammaging"** (DOI `10.1002/ctm2.70527`) profiles naturally aging mouse testes at 3, 15, 21, and 27 months. Results **"Spatiotemporal profiling links SASP-secreting TMs to Leydig niche senescence in ageing testes"** and **"CCL8 triggers testicular inflammation and functional decline"** connect age-dependent immune-niche change to reproductive decline.
- **"Midkine as a driver of age-related changes and increase in mammary tumorigenesis"** (DOI `10.1016/j.ccell.2024.09.002`) compares rat mammary glands across ages, identifies an old-age luminal progenitor state, and shows in **"Midkine treatment mimics aging-related changes"** and **"Midkine treatment promotes mammary tumor initiation"** that a candidate age-associated signal can reproduce part of the aged tissue state and increase tumor susceptibility.
- **"Sirt6 deficiency promotes senescence and age-associated intervertebral disc degeneration in mice"** (DOI `10.1038/s41413-025-00422-3`) shows a disc-specific knockout phenotype at 12 months that becomes more severe at 24 months, with increased senescence/SASP burden. This is age-progressive tissue degeneration plus genetic susceptibility.
- **"DHCR24 Deficiency Drives Age-Related Meibomian Gland Dysfunction..."** (DOI `10.7150/ijbs.129636`) starts from young-versus-two-year-old mouse gland multi-omics, then shows that meibocyte-specific deletion recapitulates gland atrophy, lipid imbalance, and inflammatory signaling and that AAV restoration improves pathology. Natural aging is the discovery context; perturbation tests a tissue mechanism.
- **"Multi-omics profiling reveals systemic rejuvenation of the aged kidney through senolytic therapy"** (DOI `10.1038/s41536-026-00490-x`) uses naturally aged mice. Results **"Long-term D+Q treatment mitigates hallmarks of renal aging"** and subsequent cell-type sections show reduced senescence markers, fibrosis, inflammation, lipotoxicity, and transcriptional age signatures.

This natural-aging stratum deserves its own identity. It should be subgrouped by whether age is the primary contrast, a modifier of intervention response, or the discovery context for a subsequent perturbation.

### 3. Cellular and tissue senescence is the largest recurring construct, but it is biologically plural

Senescence spans replicative exhaustion, stress-induced arrest, immune-cell dysfunction, post-mitotic states, acute injury, tumor suppression, and pro-tumor microenvironments. Pooling these as one mechanism would erase important directionality.

- **Replicative senescence:** **"Unveiling E2F4, TEAD1 and AP-1 as regulatory transcription factors of the replicative senescence program"** (DOI `10.1007/s13238-021-00894-z`) uses passage-resolved mouse skin fibroblasts. Results verify reduced proliferation, SA-beta-gal activity, inflammatory transcription, methylation, and chromatin-accessibility changes, then perturb TFs to attenuate parts of the program. This is a cellular aging model, not organismal aging.
- **Immune-cell senescence across age:** **"Age-independent and targetable transcription factor networks regulating CD8+ T cell senescence in aging humans"** (DOI `10.1016/j.celrep.2025.116795`) finds more SA-beta-gal-high CD8+ T cells in older donors, but multi-omics variation is driven primarily by senescence status rather than donor age. The paper explicitly shows that cell state and chronological age are related but separable.
- **Vascular senescence in age-related pathology:** **"ATF3 Deficiency Exacerbates Ageing-Induced Atherosclerosis..."** (DOI `10.1002/advs.202502249`) combines age-stratified vascular observations, SAMP8 and ApoE-knockout models, VSMC perturbations, and terazosin treatment. Results connect ATF3/autophagy to VSMC senescence, stiffness, and plaque pathology, but the models include both premature aging and diet-induced atherosclerosis.
- **Acute injury-associated senescence:** **"Inhibition of MyD88 in Tubular Epithelial Cells Alleviates the Cellular Senescence in Sepsis-Associated Acute Kidney Injury"** (DOI `10.1007/s10753-026-02526-2`) uses young mice subjected to cecal ligation and puncture plus HK-2 cells. Senescence is a stress response in acute injury, not natural kidney aging.
- **Senescence as a tumor barrier:** **"NHE7 drives endometrial cancer progression by delaying senescence..."** (DOI `10.1038/s42003-025-08296-1`) shows that reduced tumor-cell senescence can support proliferation and progression. Here, more senescence is potentially protective against tumor growth, opposite to the usual geroscience framing of senescent-cell burden as harmful.
- **Cancer-treatment context:** **"Investigating Biological Mechanisms of Radiation Resistance in Advanced Stage Cervical Cancer"** (repository DOI `10.7936/zw5q-8j61`) contains chapters on p21-mediated senescence after E6* manipulation and chemoradiation, but the thesis's primary object is radiation resistance and recurrence, not biological aging.

The Results should therefore distinguish at least: replicative senescence; natural age-associated senescent-cell accumulation; stress- or therapy-induced senescence; immune senescence; post-mitotic senescence; and tumor-suppressive versus tumor-promoting roles.

### 4. Reproductive aging contains several non-equivalent clocks

The reproductive subset should not be pooled as one "ovarian aging" mechanism.

- **Natural late-life reproductive decline:** **"A uterine-centric view of reproductive senescence...in laying hens"** (DOI `10.1002/imo2.70128`) studies 100-week hens with heterogeneous late-life laying performance. The Results/implications sections identify uterus weight as a heritable intermediate phenotype associated with late-life egg production and shell quality. This is natural reproductive senescence at an organism/tissue interface.
- **Natural male reproductive aging:** the testicular inflammaging paper (DOI `10.1002/ctm2.70527`) links age-dependent macrophage states to sperm, endocrine, and tissue decline in naturally aged mice.
- **Post-ovulatory aging:** **"Single-Cell Multi-Omics Analysis of In Vitro Post-Ovulatory-Aged Oocytes..."** (DOI `10.1016/j.mcpro.2024.100882`) defines aging as 16 hours of in-vitro culture after ovulation. Results show falling fertilization/ATP, proteome and phosphoproteome deterioration, and partial rescue by melatonin or proteasome inhibition. This is time-since-ovulation deterioration, not reproductive aging over the lifespan.
- **Treatment-induced ovarian failure:** **"Acupuncture modulates ovarian senescence...in chemotherapy-induced POF model"** (DOI `10.1016/j.exger.2025.112815`) uses young rats with cyclophosphamide-induced ovarian dysfunction. The primary construct is induced premature ovarian failure and intervention response.
- **Premature placental aging:** **"Gestational exposure to PP-NPs promotes premature placental ageing..."** (DOI `10.1016/j.jhazmat.2026.142949`) uses maternal nanoplastic exposure and trophoblast assays. Results show placental injury, fetal-growth effects, and a stress-induced senescence program; the Discussion explicitly distinguishes clinical relevance of FGR senescence markers from evidence of human PP-NP exposure.
- **Disease-specific decidual senescence:** **"HK2-driven histone H3K18 lactylation promotes stromal cell senescence and decidualization deficiency in URSA..."** (DOI `10.1186/s11658-026-00879-y`) links metabolic-epigenetic regulation to stromal-cell senescence in recurrent spontaneous abortion. It is a pregnancy pathology mechanism, not natural reproductive aging.

Recommended reproductive subgroups are natural late-life decline, gonadal reserve/failure, gamete time-since-ovulation aging, gestational/placental premature aging, and reproductive-disease cellular senescence.

### 5. Age-related diseases are endpoints, contexts, or consequences depending on the report

Age-related disease should not automatically be presented as evidence about aging itself. Full texts support three configurations:

1. **Age-dependent disease phenotype as the primary outcome.** In **"Gut-Metabolome-Proteome Interactions in Age-Related Hearing Loss"** (DOI `10.1002/advs.202514269`), Results compare 6-week and 12-month mice with measured auditory thresholds and cochlear pathology, then use FMT and an induced auditory-cell model. The age-related functional phenotype is directly measured.
2. **Natural aging process transferred into disease-like dysfunction.** In **"Aged Gut Microbiota Contributes to Cognitive Impairment and Hippocampal Synapse Loss in Mice"** (DOI `10.1111/acel.70064`), Results show that microbiota from naturally aged 100-week mice transfers cognitive and synaptic deficits to young recipients, with bacterial/metabolite rescue experiments. Aging supplies an experimentally transferable exposure.
3. **Disease linked to an aging biomarker or senescence mechanism.** In **"Subclinical atherosclerosis and accelerated epigenetic age mediated by inflammation"** (DOI `10.1093/eurheartj/ehad361`), the primary finding is an association between subclinical atherosclerosis and GrimAge acceleration in 391 middle-aged participants, with formal mediation by inflammatory signals. This is a disease-clock relation, not direct evidence that atherosclerosis accelerates whole-organism aging.

Other disease-rich clusters include osteoarthritis/cartilage, intervertebral disc degeneration, vascular disease, kidney injury and renal aging, cognitive decline, hearing/ocular dysfunction, heart failure, autoimmune disease, and multiple cancers. The narrative should state whether the aging construct is the disease phenotype, a proposed mediator, a susceptibility context, or only the motivation.

### 6. Induced and premature-aging models are common and need a visible boundary

Profile fields flagged at least 28 reports with induced/premature-aging or stress-senescence terminology. Representative full-text models include D-galactose exposure, UV-induced photoaging, TBHP-induced chondrocyte senescence, chemotherapy-induced ovarian failure, global *Bmal1* knockout, hyperammonemia, sepsis-associated injury, surgical osteoarthritis/disc models, and PP-NP-induced placental senescence.

- **"Protocatechuic Acid Alleviates D-Gal-Induced Renal Senescence..."** (DOI `10.1002/fsn3.71826`) explicitly states in the Discussion that future work should validate the findings in naturally aged or more clinically representative disease models.
- **"Multi-Omics Analysis Reveals Photodynamic Therapy Ameliorating Skin Photoaging..."** (DOI `10.1111/acel.70328`) uses UVR-treated young hairless mice and UV-treated fibroblasts. Results show improved wrinkles, barrier measures, extracellular matrix, and early senescence markers after therapy. This is extrinsic photoaging with functional tissue outcomes, not intrinsic chronological aging.
- **"Bioorthogonal epigenetic anchoring of heterochromatin..."** (DOI `10.1016/j.jare.2026.07.047`) uses TBHP-induced senescent rat chondrocytes and surgically induced osteoarthritis. Results **"BR-CARS restores heterochromatin architecture and reverses the senescent phenotype"** support reversal within these models, but not organismal rejuvenation.

Induced models are valuable for perturbation and mechanistic localization. They should not be silently merged with natural aging. A dedicated model-origin variable should classify natural chronological aging, genetic premature aging, chemical/stress induction, disease induction, and ex-vivo time-dependent deterioration.

### 7. Rejuvenation and intervention response range from survival to molecular resemblance

"Rejuvenation" is used at several evidential depths:

- **Strongest multi-level form:** youthful circulation (DOI `10.1038/s43587-023-00451-9`) combines survival, function, epigenetic clocks, and transcriptomic reversal.
- **Natural-aged organ response:** long-term D+Q in aged kidney (DOI `10.1038/s41536-026-00490-x`) combines histology, senescence, fibrosis/inflammation, metabolism, and cell-type expression, but does not establish whole-organism rejuvenation.
- **Tissue repair/function:** DHCR24 AAV restoration in meibomian gland (DOI `10.7150/ijbs.129636`), terazosin in vascular models (DOI `10.1002/advs.202502249`), and photodynamic therapy in photoaged skin (DOI `10.1111/acel.70328`) reverse defined tissue phenotypes.
- **Molecular profile shift:** **"Multi-organ metabolome biological age implicates cardiometabolic conditions and mortality risk"** (DOI `10.1038/s41467-025-59964-z`) develops organ-specific metabolomic age gaps and relates them to disease/mortality; it does not test rejuvenation. **"Sleep chart of biological ageing clocks in middle and late life"** (DOI `10.1038/s41586-026-10524-5`) maps U-shaped associations between sleep duration and 23 clock-derived age gaps, disease, and mortality. These are measurement/risk studies.

The article should use an endpoint ladder: survival; functional healthspan; organ pathology/function; cellular state; omic signature; clock value. A change lower on this ladder should not automatically inherit claims from a higher level.

### 8. Other recurring constructs should remain visible

Five profiles involve plants or fruit. These are legitimate senescence/longevity studies, but their biological meaning differs from animal geroscience.

- **"Multiomics analyses unveil the involvement of microRNAs in pear fruit senescence..."** (DOI `10.1038/s41438-020-00420-y`) defines senescence as postharvest quality deterioration and nutrient/component disassembly under high, room, or low temperature. Results map temperature-specific metabolite-miRNA-mRNA networks.
- **"Multi-omics approach reveals the contribution of KLU to leaf longevity and drought tolerance"** (DOI `10.1093/plphys/kiaa034`) treats age-dependent leaf senescence as a regulated developmental nutrient-remobilization process. Results **"KLU/KLU-dependent signaling influences leaf aging"** connect cytokinin signaling, chlorophyll retention, and leaf longevity.

Plant/fruit reports should be a separate kingdom/model stratum or sensitivity display, not woven into mammalian cellular senescence as if the outcomes were homologous by default.

Cancer-specific senescence is another recurring boundary. In some reports senescence suppresses malignant proliferation; in others senescent stromal or immune cells create a tumor-supportive environment. The direction and cell compartment must be reported.

## Species and model-system map

The following counts are nonexclusive reports whose title or graph-profile population/cohort text mentions the model. They map the available systems but may include a validation model or external dataset rather than the primary experiment.

| System signal in all 101 profiles | Reports | Narrative implication |
|---|---:|---|
| Cells or organoids | 61 | Cellular perturbation is a major evidential mode; cell-state aging must be separated from organismal aging. |
| Human participants/population or human molecular data | 57 | Includes cohorts, GWAS/QTL resources, primary cells, and clinical samples; these differ in proximity to aging phenotypes. |
| Mouse/murine | 52 | Dominant in-vivo platform, spanning natural aging, induced aging, disease models, and tissue-specific perturbation. |
| Rat | 10 | Concentrated in tissue disease, reproductive, neural, and intervention models. |
| *C. elegans*/nematode | 8 | Strongly represented in lifespan/healthspan and conserved metabolic-stress mechanisms. |
| *Drosophila* | 5 | Primarily lifespan, neural/lipid, microbiome, diet, and temperature-response studies. |
| Plant/fruit | 5 | Developmental/postharvest senescence and organ longevity; requires separate interpretation. |
| Nonhuman primate | 2 | Sparse; includes macaque/rhesus aging contexts. |
| Laying hen/chicken | 2 | Reproductive and ovarian aging/production contexts. |
| Turquoise killifish | 1 | A valuable naturally short-lived vertebrate lifespan model with a sex-specific result. |

Cross-system studies are common: human discovery plus cell perturbation; natural-aged mouse discovery plus cultured-cell mechanism; mouse omics plus worm lifespan validation; or clinical association plus animal transfer experiments. The synthesis unit should record which system supports which part of the claim rather than assign one species per report.

## Tissue and organ map

Broad, nonexclusive profile-text mentions show the following topology: blood/immune/hematopoietic (45 reports), liver/adipose/metabolic systems (34), reproductive/placental tissues (19), gut/intestine/microbiome (17), vascular/heart (14), skeletal muscle (14), cancer/tumor systems (14), skin/connective/stem-cell systems (13), bone/cartilage/joint/disc (9), brain/neural (8), lung/respiratory (6), kidney/renal (5), and hearing/ocular tissues (3). These are orientation counts from broad term groups, not final hand-coded frequencies.

Biologically, the corpus is best described as a **distributed tissue-aging map** rather than a whole-organism aging corpus. The densest recurring tissue narratives are:

- immune and inflammatory remodeling across blood, macrophages, T cells, microglia, and tissue niches;
- metabolic flexibility across liver, adipose tissue, muscle, mitochondria, and circulating metabolites;
- barrier and host-microbiome systems across gut, skin, kidney, and placenta;
- structural tissue decline across vasculature, cartilage, disc, bone, and extracellular matrix;
- reproductive aging across testis, ovary, uterus, oocyte, endometrium, and placenta.

For each report, tissue should be coded separately for discovery, omic measurement, perturbation, outcome, and validation. A blood-derived QTL used to infer a joint-disease target is not tissue-matched evidence for cartilage biology.

## Role of aging in the report

The same report can occupy more than one role. A four-way role map is preferable to a single aging label.

| Role | Operational question | Representative full-text examples |
|---|---|---|
| Primary outcome or trajectory | Is lifespan, function, age gap, natural age change, or senescence directly measured as the main outcome? | APRT killifish lifespan (`10.1016/j.devcel.2023.05.015`); natural BXD lifespan (`10.1016/j.cels.2021.09.005`); MetBAG (`10.1038/s41467-025-59964-z`); replicative fibroblast senescence (`10.1007/s13238-021-00894-z`). |
| Mechanism of tissue decline/disease | Is an aging process proposed to explain a functional or disease phenotype? | Testicular inflammaging (`10.1002/ctm2.70527`); aged microbiota and cognitive decline (`10.1111/acel.70064`); midkine and mammary tumor susceptibility (`10.1016/j.ccell.2024.09.002`). |
| Intervention context or target | Is an aged/induced-aging system used to test reversal, rescue, or response? | D+Q aged kidney (`10.1038/s41536-026-00490-x`); youthful circulation (`10.1038/s43587-023-00451-9`); photoaged skin (`10.1111/acel.70328`); heterochromatin anchoring in OA models (`10.1016/j.jare.2026.07.047`). |
| Background, modifier, or borrowed vocabulary | Is aging secondary to another primary problem, or is "senescence" a context-specific state? | Cervical-cancer radiation resistance thesis (`10.7936/zw5q-8j61`); CML treatment-free remission letter (`10.1002/ctm2.317`); tumor-cell senescence resistance in endometrial cancer (`10.1038/s42003-025-08296-1`). |

Recommended fields are `aging_object`, `biological_scale`, `temporal_form`, `role_in_claim`, `model_origin`, and `endpoint_depth`. This will prevent a report about an age-associated disease with senescence-related genes from being displayed beside a direct lifespan intervention without qualification.

## Biologically meaningful synthesis themes

These themes arise repeatedly across species and tissues, but they should be presented as response axes rather than a universal mechanism taxonomy.

### Theme A: Maintenance of adaptive metabolic and energetic capacity

The most coherent cross-species storyline is that aging involves reduced capacity to adjust energy production, substrate use, redox balance, and biosynthetic burden, while several lifespan or tissue-protective interventions restore flexibility rather than simply shifting one metabolite.

Anchors include APRT/AMP-AMPK in killifish (`10.1016/j.devcel.2023.05.015`, Results on age-related metabolic plasticity), SIRT6-dependent liver/adipose energy handling (`10.1038/s41467-021-23545-7`, Results and Discussion), reduced rRNA synthesis and energy conservation in worms (`10.1038/s41467-024-46037-w`, Results on metabolic aging), SKN-1 redox/detoxification (`10.1007/s11306-023-02022-w`, Abstract Results), and muscle *Bmal1* restoration with systemic metabolic effects (`10.1172/jci.insight.174007`, Results on glucose handling and multi-omics).

This theme is stronger than a generic "deregulated nutrient sensing" label because it preserves the measured processes and does not force all studies into a Hallmark category.

### Theme B: Senescent-state remodeling of tissue niches and inflammatory communication

Senescence matters most when linked to altered communication, extracellular matrix, immune recruitment, or loss of tissue-specific function. The recurring unit is often a cell-state-in-niche, not an isolated senescent cell.

Anchors include CCL8-high testicular macrophages (`10.1002/ctm2.70527`), CD8+ T-cell enhancer/TF remodeling (`10.1016/j.celrep.2025.116795`), VSMC phenotype switching and autophagy (`10.1002/advs.202502249`), SIRT6-deficient disc SASP (`10.1038/s41413-025-00422-3`), and senolytic remodeling of the aged kidney (`10.1038/s41536-026-00490-x`). Cancer papers demonstrate why direction must remain cell- and context-specific.

### Theme C: Inter-organ, circulating, and microbial transfer of aging phenotypes

Several of the most biologically compelling reports move beyond within-tissue correlations and manipulate a transferable exposure.

Anchors include youthful circulation (`10.1038/s43587-023-00451-9`), aged-microbiota transfer to young mice (`10.1111/acel.70064`), microbiota-derived IAA and fly lifespan (`10.1128/msystems.01665-24`, Results **"Supplementation with IAA extends lifespan in Drosophila via AhR"**), FMT in age-related hearing loss (`10.1002/advs.202514269`), and muscle-specific *Bmal1* restoration with systemic effects (`10.1172/jci.insight.174007`).

This theme supports a storyline about tissue-to-system causation and transportability. It also exposes a major gap: many circulating omic signals are measured in blood but interpreted as organ-specific without direct transfer or tissue-matched perturbation.

### Theme D: Chromatin state and biological-age measurement are related but distinct

The corpus includes both chromatin mechanisms and age-prediction systems. They should not be merged.

Mechanistic anchors include TF/chromatin remodeling in replicative fibroblast senescence (`10.1007/s13238-021-00894-z`) and structural heterochromatin-lamina restoration in induced chondrocyte senescence (`10.1016/j.jare.2026.07.047`). Measurement anchors include GrimAge in subclinical atherosclerosis (`10.1093/eurheartj/ehad361`), organ-specific MetBAGs (`10.1038/s41467-025-59964-z`), and multi-modal age gaps in the sleep study (`10.1038/s41586-026-10524-5`).

The synthesis should ask whether an intervention changes a validated predictor, a tissue molecular state, function, pathology, or survival. These are not equivalent levels of biological evidence.

## Is a separate mechanism-based Results section supported?

### Decision

**Not as a broad standalone section organized by named mechanisms.** The current exploratory corpus is too heterogeneous in biological scale, endpoint, model origin, and evidential depth. A section titled simply "Aging mechanisms" would invite three overstatements:

1. that the same pathway label has the same meaning across lifespan, clocks, natural tissue aging, cancer, acute injury, and plant senescence;
2. that cross-omics pathway convergence identifies a mechanism even when it is only associative or predictive;
3. that reversal of molecular signatures establishes tissue or organismal rejuvenation.

### What is supported

A compact final Results subsection is supported if titled **"Recurrent biological response axes across evidence strata"** or **"Biological synthesis by aging phenomenon."** It should:

- organize first by aging phenomenon and biological scale, not by Hallmark;
- show discovery/hypothesis evidence, effect-supported perturbation, and independent validation in separate columns;
- retain discordant direction, tissue, species, sex, and model-origin information;
- use the four themes above as interpretive headings only when multiple verified reports support them;
- avoid pooled frequency claims until claim-level extraction and report/study linkage are complete.

## Recommended biological storyline

The existing methods-first article architecture can be retained, but its biological map and late Results synthesis should be revised as follows.

### In the field-map Results section

Add a first-class map of:

1. aging phenomenon: organismal longevity/healthspan; natural tissue aging; cellular/tissue senescence; reproductive aging; age-related disease; induced/premature aging; intervention/rejuvenation; plant/fruit senescence;
2. role in claim: primary outcome, mechanism, intervention context, or background/modifier;
3. biological scale: cell, tissue niche, organ, physiological system, organism, population proxy;
4. model origin: natural aging, genetic premature aging, chemical/stress induction, disease induction, ex-vivo time deterioration;
5. endpoint depth: survival, function, pathology, cellular state, omic signature, clock.

### Proposed biological synthesis sequence after causal evidence and validation

1. **Organismal longevity and functional resilience.** Lead with direct survival and functional endpoints; show sex, species, and natural-versus-induced model differences.
2. **Natural tissue aging and loss of response capacity.** Cover muscle plasticity, immune/reproductive niches, metabolic flexibility, and structural organ decline.
3. **Senescence-centered pathology across tissues.** Stratify replicative, immune, stress-induced, post-mitotic, and tumor-related senescence; do not imply uniform direction.
4. **Intervention response and claims of rejuvenation.** Order evidence by the endpoint ladder from survival/function to clocks and molecular similarity.
5. **Cross-cutting response axes and transportability.** Summarize adaptive metabolism, niche/inflammatory communication, transferable systemic factors, and chromatin regulation, with evidence strata visible.

### Necessary subgroup displays

- A dedicated reproductive-aging panel with natural late-life, ovarian-failure, gamete, gestational, and disease-specific strata.
- A natural-versus-induced model column in every biological table.
- A clock/proxy panel that does not mix clock associations with direct aging outcomes.
- A kingdom/model-system sensitivity panel separating plant/fruit senescence.
- A cancer-senescence panel showing whether senescence is tumor suppressive, tumor promoting, treatment induced, or microenvironmental.
- Tissue-match and species-transport columns for every claimed biological link.

## Representative evidence anchors

| DOI and title | Relevant full-text section/evidence | Narrative use and limit |
|---|---|---|
| `10.1016/j.devcel.2023.05.015`, *Genetic perturbation of AMP biosynthesis extends lifespan...* | Results, **"Male-specific lifespan extension..."**: median and maximal lifespan increase in male but not female killifish; later Results show partial restoration of metabolic plasticity. | Direct organismal anchor; sex-specific and species-specific. |
| `10.1016/j.cels.2021.09.005`, *Multiomic profiling of the liver across diets and age...* | **"Clinical analysis of lifespan as a function of genotype and diet"**: natural-death lifespan across 1,336 female BXD mice; candidate tests in worms. | Natural lifespan and gene-environment heterogeneity; cross-species validation is not identical evidence. |
| `10.1038/s41467-021-23545-7`, *Restoration of energy homeostasis by SIRT6 extends healthy lifespan* | Discussion and liver metabolomics Results: longer lifespan in both sexes, young-like activity/pathology and liver/adipose energy handling. | Strong lifespan-plus-function anchor. |
| `10.1038/s41467-024-46037-w`, *Reducing the metabolic burden of rRNA synthesis...* | **"Levels of pre-rRNA synthesis control lifespan and healthspan"** and **"Curbed ribosome biogenesis delays metabolic aging"**. | Direct worm lifespan/function and late-life intervention; limited human-primary-cell extension. |
| `10.1038/s43587-023-00451-9`, *Multi-omic rejuvenation and lifespan extension...* | **"Long-term parabiosis...extends lifespan and healthspan"**: survival, function, blood/liver clocks, transcriptome. | Rare multi-level rejuvenation anchor; parabiosis-specific. |
| `10.1002/advs.202521633`, *The Age-Dependent Resident Myonuclear Multi-Omic Response...* | Results compare adult and aged muscle before and after acute mechanical overload. | Aging as trajectory and response modifier, not survival. |
| `10.1007/s13238-021-00894-z`, *Unveiling E2F4, TEAD1 and AP-1...* | Results on time-resolved replicative senescence and TF perturbation reducing selected senescence signatures. | Cellular senescence mechanism; no organismal aging endpoint. |
| `10.1016/j.celrep.2025.116795`, *Age-independent and targetable transcription factor networks...* | Results show SA-beta-gal-high CD8+ cells increase with age, but chromatin/transcription variation is driven mainly by senescent state. | Demonstrates age-state separability. |
| `10.1002/ctm2.70527`, *Spatiotemporal mapping reveals Ccl8hi macrophages...* | Results on 3-27-month testes and CCL8 perturbation; reproductive morphology/function and inflammaging. | Natural tissue aging and niche communication. |
| `10.1016/j.ccell.2024.09.002`, *Midkine as a driver of age-related changes...* | **"Midkine treatment mimics aging-related changes"** and **"promotes mammary tumor initiation"**. | Age-associated tissue mediator and cancer susceptibility; not lifespan. |
| `10.1038/s41413-025-00422-3`, *Sirt6 deficiency promotes senescence and age-associated intervertebral disc degeneration...* | Age-dependent disc phenotype at 12 and 24 months; Results on senescence/SASP burden. | Natural age progression modified by tissue-specific knockout. |
| `10.1038/s41536-026-00490-x`, *Multi-omics profiling reveals systemic rejuvenation of the aged kidney...* | Results on p16/p21/SA-beta-gal, fibrosis, inflammation, lipid metabolism, and cell-type age signatures after D+Q. | Multi-level organ response in natural aging; not whole-organism rejuvenation. |
| `10.1002/imo2.70128`, *A uterine-centric view of reproductive senescence...* | Cohort of 100-week hens; implications section links uterus weight to late-life egg production and shell quality. | Natural reproductive decline; production biology and species specificity. |
| `10.1016/j.mcpro.2024.100882`, *Single-Cell Multi-Omics Analysis of In Vitro Post-Ovulatory-Aged Oocytes...* | Results on 16-hour in-vitro aging, fertilization, ATP, protein degradation, and melatonin/MG132 rescue. | Gamete time deterioration; not organismal aging. |
| `10.1016/j.jhazmat.2026.142949`, *Gestational exposure to PP-NPs promotes premature placental ageing...* | Results on trophoblast/placental senescence and fetal outcomes; Discussion limits human extrapolation. | Toxicant-induced premature placental aging. |
| `10.1002/advs.202514269`, *Gut-Metabolome-Proteome Interactions in Age-Related Hearing Loss...* | Results measure auditory thresholds/cochlear pathology in 6-week and 12-month mice, then FMT and D-gal cell experiments. | Age-related functional disease plus mixed natural/induced models. |
| `10.1111/acel.70064`, *Aged Gut Microbiota Contributes to Cognitive Impairment...* | Results transfer 100-week-mouse microbiota into young recipients and test bacterial/metabolite rescue. | Transferable natural-aging exposure; cognitive and synaptic outcomes. |
| `10.1093/eurheartj/ehad361`, *Subclinical atherosclerosis and accelerated epigenetic age...* | Results on GrimAge acceleration and inflammatory mediation in 391 PESA participants. | Human clock/disease mechanism; clock is a proxy endpoint. |
| `10.1111/acel.70328`, *Photodynamic Therapy Ameliorating Skin Photoaging...* | Results on UVR-induced mouse photoaging, tissue function, matrix, and senescence after ALA-PDT. | Extrinsic induced aging with tissue outcomes. |
| `10.1002/fsn3.71826`, *Protocatechuic Acid Alleviates D-Gal-Induced Renal Senescence...* | Discussion explicitly calls for validation in naturally aged or closer disease models. | Useful induced-model boundary. |
| `10.1038/s41438-020-00420-y`, *Multiomics analyses...pear fruit senescence...* | Results define temperature-dependent postharvest senescence timing and molecular networks. | Separate plant/fruit construct. |
| `10.1093/plphys/kiaa034`, *Multi-omics approach reveals the contribution of KLU to leaf longevity...* | **"KLU/KLU-dependent signaling influences leaf aging"**: chlorophyll, cytokinin, and developmental leaf senescence. | Separate developmental plant-aging construct. |
| `10.7936/zw5q-8j61`, *Investigating Biological Mechanisms of Radiation Resistance...* | Thesis sections **"E6* overexpression induces p21 mediated cellular senescence"** and chemoradiation response. | Boundary case: cancer/radiation is primary; aging is not the central outcome. |
| `10.1038/s42003-025-08296-1`, *NHE7 drives endometrial cancer progression by delaying senescence...* | Results show NHE7 suppresses senescence markers while increasing cancer-cell proliferation. | Demonstrates opposite biological direction of senescence in tumor suppression. |

## Full-text inspection audit

The 40 checked Markdown reports were:

1. `10.1016/j.devcel.2023.05.015` - APRT, killifish lifespan and metabolic health.
2. `10.1001/jamapsychiatry.2024.1429` - psychiatric/substance liabilities, longevity, and epigenetic age.
3. `10.1007/s11306-023-02022-w` - SKN-1/Nrf2, worm lifespan, redox/detoxification.
4. `10.1016/j.celrep.2024.115099` - glial Ugt35b, fly lifespan, brain lipid homeostasis.
5. `10.1038/s41467-021-23545-7` - SIRT6, mouse lifespan/health and energy homeostasis.
6. `10.1016/j.cels.2021.09.005` - BXD natural lifespan, diet, liver multi-omics, worm validation.
7. `10.1038/s41467-024-46037-w` - rRNA synthesis, worm lifespan/healthspan.
8. `10.1038/s41467-025-61433-6` - mitochondrial translation, immunometabolic stress, worm longevity.
9. `10.1038/s43587-023-00451-9` - youthful circulation, lifespan, function, and clocks.
10. `10.1128/msystems.01665-24` - microbial IAA, AhR-Sirt2, fly lifespan.
11. `10.1002/advs.202521633` - age-dependent skeletal-muscle hypertrophic response.
12. `10.1038/s41467-025-59964-z` - organ-specific metabolomic age gaps, disease, mortality.
13. `10.1038/s41586-026-10524-5` - sleep and multi-organ biological-age clocks.
14. `10.1002/advs.202502249` - VSMC senescence, vascular aging, atherosclerosis, terazosin.
15. `10.1007/s13238-021-00894-z` - replicative fibroblast senescence.
16. `10.1016/j.ccell.2024.09.002` - natural mammary aging, midkine, tumor initiation.
17. `10.1016/j.celrep.2025.116795` - human CD8+ T-cell senescence across age.
18. `10.1016/j.jare.2026.07.047` - heterochromatin anchoring, induced chondrocyte senescence, OA.
19. `10.1038/s41413-025-00422-3` - SIRT6, age-associated disc degeneration and senescence.
20. `10.1101/2025.06.19.660635` - endothelial senescence-associated stemness and plaques.
21. `10.1172/jci.insight.174007` - muscle *Bmal1* rescue in a premature-aging model.
22. `10.1007/s10753-026-02526-2` - sepsis-AKI and tubular-cell senescence.
23. `10.1002/ctm2.70527` - natural testicular inflammaging.
24. `10.1002/imo2.70128` - late-life reproductive performance in hens.
25. `10.1016/j.exger.2025.112815` - chemotherapy-induced ovarian failure and acupuncture.
26. `10.1016/j.mcpro.2024.100882` - in-vitro post-ovulatory oocyte aging.
27. `10.1016/j.jhazmat.2026.142949` - PP-NP-induced premature placental aging.
28. `10.1186/s11658-026-00879-y` - URSA stromal senescence and decidualization.
29. `10.1002/advs.202514269` - natural age-related hearing loss, FMT, and induced cell aging.
30. `10.1111/acel.70064` - aged microbiota transfer and cognitive/synaptic decline.
31. `10.1111/acel.70328` - UV-induced photoaging and photodynamic therapy.
32. `10.7150/ijbs.129636` - natural meibomian-gland aging and DHCR24 perturbation.
33. `10.1093/eurheartj/ehad361` - subclinical atherosclerosis, GrimAge, inflammation.
34. `10.1002/fsn3.71826` - D-gal-induced renal senescence.
35. `10.1038/s41536-026-00490-x` - natural kidney aging and long-term senolytic treatment.
36. `10.1038/s41438-020-00420-y` - pear-fruit senescence.
37. `10.1093/plphys/kiaa034` - Arabidopsis leaf longevity/senescence.
38. `10.7936/zw5q-8j61` - cervical-cancer radiation resistance and treatment-related senescence.
39. `10.1002/ctm2.317` - CML clonogenicity, treatment-free remission, and replicative-senescence interpretation.
40. `10.1038/s42003-025-08296-1` - endometrial-cancer progression through delayed tumor-cell senescence.

## Bottom line for article design

The corpus supports a biologically rich evidence map, but its unifying object is not one molecular mechanism. It is the use of multi-omics and directed designs to study **different levels and meanings of aging**. The article will be clearest if it anchors claims to the measured aging object, then asks what causal evidence exists for changes in resilience, tissue state, disease susceptibility, survival, or intervention response.

Keep the methodological evidence strata as the main spine. Add a strong biological coordinate system early in Results. Replace or narrow a generic mechanism section with a phenomenon-stratified synthesis and four recurrent response axes. This gives metabolism, senescence, systemic communication, and chromatin a meaningful place without treating pathway recurrence as causal ground truth or forcing the corpus into the Hallmarks of Aging.
