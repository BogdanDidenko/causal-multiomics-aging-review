# Bottom-up empirical archetypes in the 101-report exploratory corpus

**Repository:** `/Users/bogdan.didenko/lpnu/causal-multiomics-aging-review`
**Corpus pack:** `analysis/article_design/corpus_grounding_v1.0.0`
**Purpose:** exploratory article-structure work only
**Date:** 2026-08-17

## Executive conclusion

The corpus is not naturally organized as a sequence of **discovery -> effect -> validation**. That sequence is useful for appraising individual claims, but it is too abstract to explain what most reports actually do. In the full texts, “discovery” ranges from differential-expression screening to a formal directed model, “effect” ranges from a cell-culture knockdown to an organismal intervention, and “validation” is usually a dependent follow-up experiment rather than independent same-link replication.

A simpler bottom-up account is a six-archetype map based on each report's dominant empirical logic:

| Dominant report archetype | Approximate reports, n (%) |
|---|---:|
| 1. Target-first perturbational mechanism | 48 (47.5%) |
| 2. Intervention-first response and efficacy profiling | 19 (18.8%) |
| 3. Transfer and host-ecosystem experiments | 9 (8.9%) |
| 4. Genetic quasi-experiment and target prioritization | 12 (11.9%) |
| 5. Age/environment mapping with candidate follow-up | 8 (7.9%) |
| 6. Clocks, mediation, and prediction | 5 (5.0%) |
| **Total** | **101 (100%)** |

These are **report-level, mutually exclusive dominant-logic assignments made for this exploratory analysis**, not final study classifications, eligibility decisions, PRISMA counts, causal levels, or judgments that every claim in a report belongs to the same evidence stratum. Hybrid reports were assigned to the workflow that organizes their main empirical argument.

The most readable Results sequence is therefore:

1. corpus composition and the six empirical archetypes;
2. experimental manipulation, moving from target-first to intervention-first to transfer/ecosystem designs;
3. population-level inference, moving from genetic quasi-experiments to age maps and clocks/mediation;
4. what omics contributes within each archetype;
5. claim-level identification, validation independence, and transportability;
6. recurrent biological mechanisms only after these design constraints are visible.

## Scope and method

### Inputs used

I analyzed all 101 entries in:

- `eligible_graph_manifest_101.csv`;
- `eligible_graph_profiles_101.jsonl`;
- `corpus_graph_summary.json`.

The manifest resolved 101/101 deterministic Docling Markdown paths. I reduced graph data to paper-level presence/combination counts so that multiple nodes in one report were not mistaken for multiple reports. I then assigned every report to one dominant empirical archetype using title, profile content, stated exposure/intervention, model, outcome, and omics role.

Only after completing that clustering did I read `analysis/article_design/article_structure_working_synthesis_v1.1.0.md` and compare its proposed architecture with the bottom-up result.

### Evidence safeguard

Luna Light nodes were used only to orient the quantitative inventory and select reports for inspection. Their `design_family`, `identification_status`, aging roles, and causal labels were **not accepted as ground truth**. Conclusions below were checked against 38 strategically selected full-text Markdown records spanning all graph-listed design families, major model systems, aging constructs, and publication formats. The checked set included human cohorts and trials; human cells and organoids; mice, rats, hens, killifish, *Drosophila*, and *C. elegans*; plants; full articles, preprints, conference abstracts, and the one supplementary-only Markdown record.

### Boundary conditions

This analysis does not alter eligibility, report linkage, PRISMA denominators, or final causal levels. Counts below describe the exploratory 101-report pack. They should not be transferred into the final manuscript without the planned claim-level extraction and report-to-study linkage.

## Quantitative map of all 101 profiles

### Corpus and graph volume

| Quantity | Value |
|---|---:|
| Reports | 101 |
| Reports with canonical graph | 101 |
| Reports with at least one causal-analysis candidate | 100 |
| Reports with no causal-analysis candidate | 1 |
| Aging-construct nodes | 686 |
| Omics-layer nodes | 437 |
| Causal-analysis nodes | 312 |
| Causal-analysis candidates per report | median 3, mean 3.09, range 0-9 |
| Reports with multiple successful graph candidates | 11 |

The node totals demonstrate why report-level reduction is necessary: a single report often contributes several exposures, interventions, outcomes, and supporting analyses.

### Candidate design-family presence at report level

These are non-exclusive graph-derived orientation counts, not verified causal classifications.

| Candidate design family | Reports with >=1 candidate, n (%) |
|---|---:|
| Direct perturbation | 73 (72.3%) |
| Non-randomized intervention | 40 (39.6%) |
| Randomized intervention | 18 (17.8%) |
| Genetic instrument | 14 (13.9%) |
| Formal mediation | 5 (5.0%) |
| Temporal identification | 4 (4.0%) |
| Other formal causal design | 3 (3.0%) |
| DAG/SCM | 1 (1.0%) |

The most frequent paper-level combinations were direct perturbation plus non-randomized intervention (28 reports), direct perturbation alone (26), genetic instrument alone (10), direct perturbation plus randomized intervention (8), randomized intervention alone (7), and non-randomized intervention alone (5). This already points away from a discovery-led field: experimental manipulation is the modal behavior.

The sole graph-labeled DAG/SCM record illustrates the danger of treating the labels as the organizing truth. In `10.26599/fshw.2026.9251125`, *Unraveling the Key Pathways through Cordycepin Prolongs Lifespan in C. elegans by Integrating Multi-omics Approaches*, the full text is organized around cordycepin dosing, lifespan/healthspan assays, multi-omics, and genetic epistasis. The DAG/network component is supporting analysis, not the report's empirical identity (Abstract; Methods, “Lifespan assays”; Results).

### Omics-layer presence at report level

These counts are also non-exclusive.

| Omics layer | Reports, n (%) |
|---|---:|
| Transcriptomics | 90 (89.1%) |
| Proteomics | 60 (59.4%) |
| Metabolomics | 46 (45.5%) |
| Epigenomics | 35 (34.7%) |
| Genomics | 21 (20.8%) |
| Other molecular omics | 15 (14.9%) |
| Lipidomics | 11 (10.9%) |
| Microbiomics | 9 (8.9%) |
| Metagenomics | 3 (3.0%) |

Transcriptomics is nearly ubiquitous, but the full texts show that its function differs by archetype: discovery screen, post-perturbation readout, cell-state definition, clock input, QTL source, pathway localization, or cross-species bridge. Omics modality alone is therefore a poor Results hierarchy.

### Aging-role candidate presence

| Graph-derived aging role | Reports, n (%) |
|---|---:|
| Aging outcome or trajectory | 94 (93.1%) |
| Aging mechanism | 86 (85.1%) |
| Aging intervention target | 49 (48.5%) |
| Longevity or healthspan | 48 (47.5%) |
| Age context only | 29 (28.7%) |
| Aging context only | 1 (1.0%) |

These labels are broad and frequently co-occur. Full-text inspection showed distinct endpoints hidden within “aging”: lifespan, healthspan, molecular-clock change, natural tissue aging, induced cellular senescence, reproductive senescence, organ disease, treatment-induced senescence, and plant/fruit senescence.

### Model systems and publication formats

A non-exclusive keyword inventory of profile titles and model descriptions found 49 reports mentioning mice, 36 cell/organoid systems, 35 human cohorts or participants, 10 rats, 7 *C. elegans*, and 5 *Drosophila*. The pack also contains a killifish study, two laying-hen studies, multiple plant/fruit studies, and cross-species programs. These are orientation counts because model descriptions came partly from graph candidates.

Full-text and DOI/header checks identified approximately 90 full articles, 4 preprints, 6 conference abstracts, and 1 record whose deterministic Markdown contains only supplementary figure legends. These are report formats, not eligibility changes.

### What the candidate “validation” data imply

The graph pack marks some validation in 94 reports and some independent-cohort validation in 15, but only 7 reports contain a validation candidate labeled `independent`; 64 have `partially_independent` and 56 have `not_independent` validation candidates. Paper-level candidate types include orthogonal perturbation (67), triangulation (52), replication (17), independent cohort (15), and negative control (5).

Even before adjudication, this distribution shows that “validation” is not a natural third study type. It is a cross-cutting property with varying target alignment and data independence.

## Archetype 1: Target-first perturbational mechanism

**Operational definition.** The report's main question is whether a named gene, RNA, protein, enzyme, transcription factor, pathway, or cellular program changes an aging-relevant phenotype. Loss/gain of function, RNAi/siRNA, CRISPR, conditional knockout, overexpression, inhibitor/agonist, rescue, or epistasis is the central empirical move. Omics is used before perturbation to nominate the target, after perturbation to localize consequences, or both.

**Approximate count.** 48/101 reports. This includes model-organism lifespan mechanisms, cell/tissue senescence mechanisms, and disease-focused target pipelines. It is the largest and most internally diverse archetype.

**Typical intervention/exposure.** Gene knockout or knockdown; overexpression; pathway inhibition; induced senescence followed by target perturbation; rescue or epistasis; occasionally a compound whose primary role is to probe a specific pathway.

**Typical omics role.** Target nomination from age/state contrasts; post-perturbation transcriptome/proteome/metabolome/lipidome readout; cell-state localization; pathway and cross-layer mechanism construction.

**Typical aging endpoint.** Organismal lifespan/healthspan in worms, flies, fish, or mice; cellular senescence markers and function; tissue degeneration; age-related disease severity; occasionally a clock or molecular-age signature.

**Representative full-text examples.**

- `10.1016/j.devcel.2023.05.015`, *Genetic perturbation of AMP biosynthesis extends lifespan and restores metabolic health in a naturally short-lived vertebrate*. CRISPR-generated `APRT` loss of function is the organizing manipulation; male heterozygotes had an approximately 17% higher median lifespan, followed by transcriptomic, metabolomic, and lipidomic localization (Results, “Male-specific lifespan extension in APRT D8/+ heterozygous fish”). The sex-specific effect is part of the finding, not generic validation.
- `10.1038/s41467-024-46037-w`, *Reducing the metabolic burden of rRNA synthesis promotes healthy longevity in Caenorhabditis elegans*. `tif-1A` overexpression and RNAi, `ncl-1` RNAi, pharmacological Pol I inhibition, and age-resolved proteomics/lipidomics test whether pre-rRNA synthesis controls lifespan and healthspan (Results, “Levels of pre-rRNA synthesis control lifespan and healthspan”).
- `10.1016/j.celrep.2024.115099`, *The glial UDP-glycosyltransferase Ugt35b regulates longevity by maintaining lipid homeostasis in Drosophila*. A prior age-expression screen nominates `Ugt35b`; glial RNAi, lipidomics, proteomics, transcriptomics, and `Lsd-2` rescue link the target to lipid droplets and lifespan (Results, “Ugt35b is highly expressed in glia and is required for Drosophila lifespan”; “Knockdown ... leads to global alterations in lipid content”).
- `10.1016/j.celrep.2025.116795`, *Age-independent and targetable transcription factor networks regulating CD8+ T cell senescence in aging humans*. Sorted human CD8+ T-cell multi-omics defines a senescence-associated regulatory state; TF inhibition/knockdown tests AP1, KLF5, and RUNX2 and partially restores stimulation response (Summary; Results, “Rational targeting of the TF network ...”).
- `10.1038/s43587-026-01100-7`, *Multiomic single-cell perturbation screens reveal critical lncRNA regulators of senescence*. A CRISPR-dCas9-KRAB Perturb-seq/multiome screen directly perturbs 32 candidate lncRNAs and measures transcriptional and chromatin effects (Abstract).

**Main inferential limitation.** A perturbation can support a within-system contrast without showing that the target naturally initiates aging, mediates an upstream exposure, or will transport to another tissue/species. Off-target effects, developmental compensation, dose non-equivalence, and rescue within the same experimental system also limit generalization. Omics measured after perturbation usually localizes downstream response; it does not by itself identify mediation. Human disease papers in this archetype often combine public-data nomination with a small number of in-vitro/in-vivo validations, leaving translation and same-link independence unresolved.

## Archetype 2: Intervention-first response and efficacy profiling

**Operational definition.** A drug, nutrient, herbal preparation, exercise program, procedure, senolytic, phototherapy, or other administered intervention is the primary organizing contrast. Multi-omics characterizes response, proposes mechanism, or supplies a molecular aging endpoint. Target perturbations, when present, support interpretation rather than define the study.

**Approximate count.** 19/101 reports.

**Typical intervention/exposure.** Senolytics, losartan, bisphosphonates, plasma exchange, acupuncture, dietary supplements, exercise, photodynamic therapy, geroprotective small molecules, or treatments of an induced aging/senescence model.

**Typical omics role.** Before/after or treated/control response signature; pathway prioritization; responder biomarker discovery; molecular-age or senescence endpoint; cross-species concordance.

**Typical aging endpoint.** Tissue senescence, molecular clocks, “youthful” omics signatures, organ function, survival, reproductive function, or age-related disease phenotype.

**Representative full-text examples.**

- `10.1038/s41536-026-00490-x`, *Multi-omics profiling reveals systemic rejuvenation of the aged kidney through senolytic therapy*. Naturally aged mice received biweekly dasatinib plus quercetin for eight months; renal senescence/fibrosis, proteomics, and single-cell transcriptional aging were compared with old vehicle and young controls (Results; Figure 1 study design).
- `10.1111/acel.70103`, *Multi-Omics Analysis Reveals Biomarkers That Contribute to Biological Age Rejuvenation in Response to Single-Blinded Randomized Placebo-Controlled Therapeutic Plasma Exchange*. This is a small randomized feasibility trial in adults over 50, with plasma-exchange regimens, placebo, 36 epigenetic clocks, and other omics (Abstract; Results, “TPE Induces Biological Age Rejuvenation ...”). The paper itself reports that no within-group clock change survived correction, no clinically meaningful outcomes were assessed, and nominal signals were explored because of low sample size (Results; Discussion/limitations).
- `10.1111/acel.70498`, *Multi-Omics Reveals Mechanisms of Metabolic Rejuvenation in Aged Mice and Pre-Frail Older Men by Losartan*. Targeted metabolomics/proteomics compare young, aged, and losartan-treated mice, then examine data from a phase II randomized trial in older men; receptor knockout mice probe target dependence (Results, mouse intervention; Results, human trial; cross-species integration).
- `10.1016/j.exger.2025.112815`, *Acupuncture modulates ovarian senescence through metabolic reprogramming*. Rats with chemotherapy-induced ovarian failure were randomized to control, model, Progynova, or acupuncture groups; ovarian metabolomics and proteomics follow phenotypic assessment (Methods, “Animals and experimental design”; Results).
- `10.26599/fshw.2026.9251125`, *Unraveling the Key Pathways through Cordycepin Prolongs Lifespan in C. elegans by Integrating Multi-omics Approaches*. Cordycepin dose-response and lifespan/healthspan assays precede microbiome, transcriptomic, metabolomic, and genetic pathway tests (Abstract; Methods, “Lifespan assays”).

**Main inferential limitation.** Treated/control omics differences are response signatures, not automatically mediators. Many studies are small, preclinical, unblinded, or use induced senescence rather than natural aging. Multiple components in herbal or procedural interventions weaken specificity. Clock or pathway reversal does not establish functional rejuvenation; clinical transport requires prespecified outcomes, adequate power, and replication.

## Archetype 3: Transfer and host-ecosystem experiments

**Operational definition.** The main causal move changes an organism's biological environment by transferring microbiota, circulation, cells, or microbial products, or by manipulating a host-microbe-metabolite axis. Unlike ordinary intervention studies, the transferred/ecological system is multicomponent and the report's mechanism depends on donor-host or host-microbiome interaction.

**Approximate count.** 9/101 reports.

**Typical intervention/exposure.** Fecal microbiota transplantation, antibiotic depletion and recolonization, bacterial supplementation, microbial metabolite supplementation, youthful circulation/parabiosis, plasma or cell transplantation, and host-glycan manipulation in organoid/fermentation models.

**Typical omics role.** Identify donor/recipient community shifts; connect microbial functions to circulating or tissue metabolites/proteins; nominate a mediator for targeted follow-up; quantify systemic or tissue rejuvenation after transfer.

**Typical aging endpoint.** Cognitive decline, hearing loss, intestinal stemness/barrier function, organismal lifespan, epigenetic age, healthspan, or age-donor-dependent regenerative function.

**Representative full-text examples.**

- `10.1111/acel.70064`, *Aged Gut Microbiota Contributes to Cognitive Impairment and Hippocampal Synapse Loss in Mice*. Microbiota from naturally aged mice transferred cognitive impairment and synapse loss to antibiotic-conditioned young recipients; metagenomics, metabolomics, and hippocampal proteomics nominated *Bifidobacterium pseudolongum* and related metabolites (Abstract; Results 2.1-2.2). The authors explicitly note that other bacteria and synergistic interactions remain unresolved (Discussion, “Limitations”).
- `10.1002/advs.202514269`, *Gut-Metabolome-Proteome Interactions in Age-Related Hearing Loss*. Germ-free mice received fecal microbiota, after which metagenomics, cochlear metabolomics/proteomics, and a D-galactose HEI-OC1 model prioritized and tested 5-HTP (Abstract; Results 2.2-2.9). The limitations call for mono-colonization to establish which species regulate tryptophan/5-HTP and direct causality (Discussion).
- `10.1038/s43587-023-00451-9`, *Multi-omic rejuvenation and lifespan extension upon exposure to youthful circulation*. Old mice underwent three months of heterochronic parabiosis followed by detachment; lifespan, physiology, DNA methylation clocks, and RNA-seq were measured (Abstract; Results, “Long-term parabiosis ... extends lifespan and healthspan”). The Discussion notes possible cellular chimerism, surgical stress, and altered physical activity.
- `10.1128/msystems.01665-24`, *Microbiota-derived indole acetic acid extends lifespan through the AhR-Sirt2 pathway in Drosophila*. Age-associated microbiome/metabolite changes lead to bacterial colonization, IAA supplementation, AhR mutation, and Sirt2 perturbation with lifespan/healthspan readouts (Introduction summary; Results, “Supplementation with IAA extends lifespan ...”).
- `10.64898/2026.07.09.736798`, *Senescence-associated loss of intestinal alpha1,2-fucose disrupts a modifiable host-microbiome homeostasis axis in people with HIV*. Cross-sectional human tissue/stool multi-omics is followed by fermentation and organoid perturbations. The full text explicitly states that the human data cannot establish temporal direction and that organoids do not recapitulate the intact mucosa (Abstract; Results; “Limitations of the study”).

**Main inferential limitation.** A transfer perturbs many linked organisms, molecules, immune signals, and behaviors simultaneously. Antibiotic conditioning, cage/donor effects, surgery, chimerism, and recipient context can be part of the effective treatment. Multi-omics can nominate a mediator, but necessity and sufficiency generally require isolate/mono-colonization, metabolite add-back, host-target perturbation, and independent replication.

## Archetype 4: Genetic quasi-experiment and target prioritization

**Operational definition.** Human inherited variation is used as an instrument or integrative anchor to prioritize exposures, genes, proteins, metabolites, immune traits, or drug targets for longevity, epigenetic aging, biological-age measures, senescence-linked disease, or age-related outcomes. MR, SMR/HEIDI, TWAS, colocalization, and QTL integration are the central inferential engine. Wet-lab expression or perturbation can be appended, but the report's candidate set and direction are genetics-led.

**Approximate count.** 12/101 reports.

**Typical intervention/exposure.** Genetically predicted behavior, expression, methylation, protein abundance, metabolite abundance, immune-cell phenotype, or target modulation.

**Typical omics role.** Supply exposure instruments through eQTL/mQTL/pQTL/metabolite-QTL data; define aging outcomes; colocalize signals; prioritize tissues, genes, and drug targets; occasionally validate expression or function downstream.

**Typical aging endpoint.** Lifespan/parental lifespan, multivariate longevity, healthspan, epigenetic age acceleration, multi-organ biological-age gaps, or senescence-linked age-related disease.

**Representative full-text examples.**

- `10.1001/jamapsychiatry.2024.1429`, *Major Psychiatric Disorders, Substance Use Behaviors, and Longevity*. Two-sample and multivariable MR estimate associations of genetic liabilities with longevity and epigenetic age; transcriptomic imputation and cis-protein MR nominate smoking-related genes and targets (Abstract; Methods, “MR Assumptions” and “Reporting and Interpreting Results”; Results, “Associations ... With Longevity”). The authors frame estimates as genetic liability and list ancestry, time-varying exposure, pleiotropy, sample overlap, and cross-sectional transcriptomic limitations.
- `10.1038/s41467-023-37729-w`, *Multi-omic underpinnings of epigenetic aging and human longevity*. TWAS, fine-mapping, colocalization, drug-target MR, metabolome-wide MR, and immune-trait MR integrate EAA and multivariate longevity (Introduction; Results). The Discussion notes cis-eQTL restriction, loss of tissue specificity, and expression-protein distance.
- `10.1111/acel.13497`, *A trans-omic Mendelian randomization study of parental lifespan uncovers novel aging biology and therapeutic candidates*. TWAS and MR screen gene expression, plasma proteins, and metabolites against parental lifespan, then use PheWAS for target prioritization (Abstract; Results 2.1-2.2). Limitations include survivor/reproductive selection, self-reported parental lifespan, environmental mismatch across generations, and instrument limitations.
- `10.3389/fendo.2025.1661666`, *Investigating the causal role of cellular senescence-related genes in preeclampsia*. SMR/HEIDI and colocalization across eQTL/mQTL/pQTL data prioritize genes, followed by placental RT-PCR (Abstract; Methods, “Study design”). Expression confirmation does not independently validate the same genetically instrumented effect.
- `10.1186/s12964-026-02985-y`, *Multi-omics and experimental evidence in human chondrocytes identify caspase-8 ... in osteoarthritis*. Public human transcriptomics, primary-chondrocyte inhibition/knockdown, proteomics, and MR/SMR form an unusually hybrid genetics-led triangulation pipeline (Abstract; Methods, “Study design”). The different components support related but not automatically identical causal links.

**Main inferential limitation.** MR/SMR/TWAS conclusions depend on relevance, independence, exclusion restriction, colocalization, tissue/source validity, ancestry, and sample overlap. Lifelong genetic liability is not the same intervention as changing an exposure or target in later life. Molecular QTL effects may be tissue-mismatched, and expression validation or pathway coherence is not independent replication of the instrumented link.

## Archetype 5: Age/environment mapping with candidate follow-up

**Operational definition.** The primary object is a multi-omic map across age, time, diet, temperature, stress, or an induced aging trajectory. The report first estimates state- or time-dependent molecular structure, interactions, or signatures. It may perturb one or two candidates afterward, often in another model, but the map rather than the perturbation organizes the paper.

**Approximate count.** 8/101 reports.

**Typical intervention/exposure.** Chronological age, natural lifespan sampling, diet-by-age factorial exposure, post-ovulatory time, storage temperature, nitrogen condition, training/disuse time course, or acute hypertrophic stimulus at different ages.

**Typical omics role.** Build trajectories and co-expression/co-abundance modules; separate age from diet/stress; nominate conserved genes or pathways; compare molecular response capacity by age.

**Typical aging endpoint.** Natural lifespan, tissue aging, age-dependent response/adaptation, reproductive/fruit/leaf senescence, or organ-disease progression with age.

**Representative full-text examples.**

- `10.1016/j.cels.2021.09.005`, *Multiomic profiling of the liver across diets and age in a diverse mouse population*. The core resource profiles BXD mouse liver transcriptome, proteome, and metabolome across age, diet, genotype, and sex; *C. elegans* ortholog knockdowns follow candidate selection (Summary; Results, “Clinical analysis of lifespan as a function of genotype and diet”). The Discussion recognizes the gap between stable candidate selection and mechanistic validation.
- `10.1186/s40364-023-00458-9`, *The essential roles of FXR in diet and age influenced metabolic changes and liver disease development*. An age-by-diet-by-FXR genotype design maps transcriptomic, metabolomic, bile-acid, and microbiome changes as liver disease progresses (Abstract; Results; Discussion). The authors state that novel molecular roles remained to be validated phenotypically in other models.
- `10.1038/s41438-020-00420-y`, *Multiomics analyses unveil the involvement of microRNAs in pear fruit senescence under high- or low-temperature conditions*. High, room, and low storage temperatures create distinct senescence times; microRNAome, transcriptome, and metabolome profiles define candidate networks, with transient transformation as follow-up (Abstract; Results, “Experimental design and postharvest treatments”).
- `10.4081/ejtm.2026.14960`, conference abstract *FES in mice, rats and men: adaptation and recovery in aging rodent muscle*. The relevant abstract describes young/old rodent training time courses and transcriptome/proteome response adaptation, but it is embedded in a 449-kB proceedings collection and synthesizes several prior datasets rather than presenting one fully reported study (Abstract 009).

**Main inferential limitation.** Age is entangled with survival, cohort, development, cumulative exposure, and tissue composition; destructive sampling is often cross-sectional. Diet/stress/time effects can be statistically separated within a factorial model without identifying a biological mediator. Candidate perturbation in a different species or cell system supports plausibility but may not test the same age-dependent link.

## Archetype 6: Clocks, mediation, and prediction

**Operational definition.** A derived biological-age score, trajectory, mediator, or prognostic model is the main output or intermediate. The central methods are clock construction/application, flexible trajectory modeling, statistical mediation/SEM, or supervised prediction rather than a direct biological perturbation.

**Approximate count.** 5/101 reports.

**Typical intervention/exposure.** Sleep duration, subclinical disease burden, lifestyle, genotype, anatomical intermediate phenotype, or clinical/cancer features. Usually no administered intervention.

**Typical omics role.** Features for age prediction; construction of organ-specific age gaps; mediator candidates; pathway interpretation; risk stratification.

**Typical aging endpoint.** Predicted biological age/age acceleration, disease/mortality risk, late-life reproductive performance, or prognosis rather than direct lifespan manipulation.

**Representative full-text examples.**

- `10.1038/s41586-026-10524-5`, *Sleep chart of biological ageing clocks in middle and late life*. UK Biobank sleep duration is related nonlinearly to 23 imaging-, proteomic-, and metabolomic-derived age gaps; sensitivity analyses, smaller external datasets, mediation, and MR are layered afterward (Introduction; Results, “Twenty-three biological ageing clocks”; Discussion, “Limitations”). The U-shaped association is observational even when genetically informed analyses are added.
- `10.1093/bib/bbag271`, *StackAge: an ensemble-based clock for precise quantification of biological age using multi-omics data*. Proteomic and metabolomic data from UK Biobank train an ensemble age predictor and disease-risk model, with SHAP interpretation and lifestyle mediation (Abstract; Methods/model development). Accurate age/risk prediction does not establish that high-importance features cause aging.
- `10.1093/eurheartj/ehad361`, *Subclinical atherosclerosis and accelerated epigenetic age mediated by inflammation*. In 391 participants, methylomic age acceleration is associated with imaging-defined atherosclerosis and transcript/protein inflammatory mediators (Abstract, “Methods and results”; Conclusion). The mediation is based on an observational cohort and remains sensitive to temporal ordering and unmeasured confounding.
- `10.1002/imo2.70128`, *A uterine-centric view of reproductive senescence*. In 254 aged laying hens, GWAS and transcriptomics are combined with statistical mediation through uterus weight for late-life egg outcomes (Graphical Abstract; “Statistical mediation analysis ...”). The authors describe decomposition of genetic associations; the intermediate phenotype is not experimentally manipulated.

**Main inferential limitation.** Prediction accuracy, feature importance, and age correlation do not identify biological aging mechanisms. Clock changes can reflect model calibration, tissue composition, or exposure-responsive biomarkers without functional rejuvenation. Statistical mediation needs well-supported temporal ordering and no unmeasured mediator-outcome confounding; cross-sectional mediation is especially vulnerable. The one supplementary-only record cannot be reliably characterized from its deterministic Markdown.

## Hybrids, duplicates, and records that do not fit cleanly

### Hybrid reports

The boundaries above are intentionally porous. Important hybrids include:

- `10.1186/s12964-026-02985-y` and `10.1186/s12967-026-07766-2`: genetics-led target nomination plus wet-lab perturbation and spatial/single-cell localization. They were placed with genetic quasi-experiments because the candidate and causal direction are introduced through SMR/MR, but much of the paper reads like target-first mechanism.
- `10.1111/acel.70498`: intervention-first losartan study with receptor knockout and a human randomized-trial dataset.
- `10.1016/j.cels.2021.09.005`: an age/diet resource map with cross-species target perturbation.
- `10.1038/s41586-026-10524-5`: clock/trajectory paper with mediation, genetic correlation, and MR.
- `10.26599/fshw.2026.9251125`: intervention-first lifespan study with network pharmacology, a graph model, multi-omics, and genetic epistasis.

These hybrids are precisely why archetypes should orient the reader but not replace claim-level design coding.

### Likely report dependence or duplicate study programs

Counts are reports, not independent studies. Full-text/title inspection suggests at least the following report-level dependencies that require formal linkage later:

- `10.1002/advs.202521633` and `10.1101/2025.10.29.685384`: article/preprint versions of the age-dependent myonuclear hypertrophy study.
- `10.1038/s43587-023-00451-9` and `10.1093/geroni/igad104.1942`: full article and conference abstract on youthful circulation/parabiosis.
- `10.1101/2025.06.19.660635` and `10.1161/circresaha.125.327427`: closely overlapping LATS1/2-CD38 endothelial senescence/atherothrombosis program.
- `10.21203/rs.3.rs-1264931/v1` and `10.26508/lsa.202201492`: closely overlapping UPL3/UBP12 plant-senescence program.

No report was removed or count changed here.

### Poor-fitting or low-information records

The following records fit the six bins only provisionally or sit at the corpus boundary:

1. `10.21037/tcr-2026-1-0264`, *A senescence-based machine learning model prognosticates and personalizes therapy in cervical cancer*. The deterministic Markdown contains only supplementary figure legends; the profile has no causal-analysis candidate. It is provisionally placed with clocks/prediction, but full-text behavior cannot be validated from the supplied Markdown.
2. `10.4081/ejtm.2026.14960`, *FES in mice, rats and men ...*. The deterministic file is an entire conference proceedings collection; Abstract 009 is identifiable, but the report is a compressed synthesis of several training datasets rather than a fully described primary experiment.
3. `10.1093/geroni/igaa057.414`, `10.1093/geroni/igac059.2661`, `10.1093/geroni/igad104.1942`, `10.1093/geroni/igae098.2630`, and `10.1093/geroni/igaf122.3850` are conference abstracts. They can be oriented to an archetype, but their abbreviated methods make omics role, study independence, and inferential limitations harder to adjudicate.
4. Plant/fruit senescence records (`10.1038/s41438-020-00420-y`, `10.1093/plphys/kiaa034`, `10.21203/rs.3.rs-1264931/v1`, `10.26508/lsa.202201492`, `10.3390/plants14152388`) form a coherent experimental niche, but developmental/harvest senescence and leaf longevity do not map cleanly onto mammalian biological-age concepts.
5. Several oncology or disease-focused records primarily study treatment-induced or tumor-cell senescence rather than organismal aging, including `10.1002/ctm2.317`, `10.1038/s42003-025-08296-1`, `10.1186/s12967-026-07766-2`, `10.20892/j.issn.2095-3941.2025.0691`, `10.3389/fimmu.2026.1718849`, `10.3389/fimmu.2026.1762222`, `10.3892/or.2026.9080`, and `10.7936/zw5q-8j61`. They fit target-first mechanism, but their aging endpoint is often a cell state embedded in disease biology.
6. Agricultural reproductive-senescence reports (`10.1002/imo2.70128`, `10.1016/j.psj.2026.107043`) are empirically clear but use productivity/end-organ phenotypes that need careful conceptual separation from whole-organism healthspan.

These are “does not fit cleanly” flags for narrative construction, not exclusion recommendations.

## Is discovery/effect/validation natural?

### Test 1: Does it recover common report workflows?

Only partially. Formal directed discovery is rare in the pack: one report has a DAG/SCM candidate, five have formal mediation, and four have temporal-identification candidates. By contrast, 73 reports have a direct-perturbation candidate and 58 have a randomized or non-randomized intervention candidate. Most papers begin with an aged/diseased contrast or a named target/intervention, not a formal causal-discovery procedure.

“Discovery” is also semantically unstable in the full texts. It can mean differential expression, network pharmacology, a co-expression module, a TWAS hit, a clock feature, a microbial correlation, a single-cell state, or a formally oriented edge. Treating all of these as one primary stratum would obscure rather than explain the corpus.

### Test 2: Is “effect” a report type?

No. An assessable effect is a claim-level property. One report can contain a randomized treatment contrast, a direct genetic perturbation, post-treatment omics associations, and an untested mechanistic chain. Labeling the whole report “effect” erases those internal differences. It remains essential for claim-level extraction and appraisal.

### Test 3: Is “validation” a mutually exclusive final phase?

No. The graph candidates mark validation in 94 reports, but only 7 reports have any candidate labeled independent. In the full texts, rescue, orthogonal assay, second omics layer, another tissue, another species, expression confirmation, and external cohort reuse are all called or treated as validation. They do not necessarily test the same normalized causal link, and many share data, investigators, systems, or target-selection steps.

### Verdict

`discovery -> effect -> validation` is **too abstract as the primary Results narrative but useful as a secondary claim-appraisal grid**:

- retain discovery versus assessable effect at the `causal_analysis_id` level;
- retain validation as an overlay requiring same-link and independence judgments;
- introduce the corpus first through the six empirical archetypes;
- do not infer a sequential pipeline when many papers are target-first, treatment-first, or map-first.

## Simplest Results-section sequence

### 3.1 Corpus composition, report linkage, and empirical archetypes

State the report/study/analysis/link units; show publication formats, systems, aging constructs, and the six dominant workflows. Flag linked reports and low-information formats. This lets the reader understand what the corpus contains before seeing causal-level judgments.

### 3.2 Experimental manipulation: target, treatment, and transferable environment

Present Archetypes 1-3 as a continuum:

1. target-first gene/pathway perturbation;
2. intervention-first response/efficacy;
3. transfer/ecosystem manipulation.

Within each, distinguish organismal lifespan/healthspan, natural tissue aging, induced senescence, and disease-cell senescence. Report the role of omics and the actual comparator before causal interpretation.

### 3.3 Population and trajectory inference

Present Archetypes 4-6:

1. genetic quasi-experiment/target prioritization;
2. age/environment mapping;
3. clocks, mediation, and prediction.

This makes the contrast between inherited instruments, observational trajectories, and predictive scores explicit.

### 3.4 What multi-omics contributes

Cross-tabulate archetype against omics function: exposure/instrument source, target nomination, post-perturbation readout, mediator candidate, clock input, mechanistic localization, or validation measurement. This is more informative than listing modality combinations alone.

### 3.5 Claim-level identification and validation

Now apply discovery versus assessable-effect strata to each causal analysis, then overlay diagnostics, same-link match, data independence, null/conflicting evidence, and transportability. This is where the strongest parts of the existing working synthesis belong.

### 3.6 Recurrent mechanisms and research gaps

Only after design and credibility are visible should the Results synthesize pathways such as metabolism, senescence/inflammation, proteostasis, mitochondrial function, host-microbiome signaling, and epigenetic regulation. Each mechanism should display which archetypes, systems, endpoints, and evidence strata support it.

## Comparison with `article_structure_working_synthesis_v1.1.0.md`

### Elements supported by the bottom-up analysis

- Keep four linked units (`report -> study/cohort -> causal analysis -> normalized link`). The apparent duplicate report programs make this essential.
- Keep validation cross-cutting rather than a mutually exclusive third study type.
- Keep omics role, aging measurement, design family, and credibility as orthogonal axes.
- Keep prediction separate from causal identification and avoid equating clock change with rejuvenation.
- Keep mechanism synthesis late, after design and validation constraints.
- Keep design-specific appraisal rather than a single quality score.

### Elements that should be revised

- The proposed Results order “formal causal hypotheses and discovery” before “causal-effect evidence” gives formal discovery more narrative weight than the corpus warrants. The field is dominated by perturbational and intervention workflows.
- “Randomized, quasi-experimental, and direct perturbation designs” is too broad as one subsection. Target-first mechanisms, intervention-first response studies, and transfer/ecosystem experiments have different questions, omics functions, endpoints, and failure modes.
- The “evidence landscape” should begin with empirical archetypes and systems, then add evidence strata. A design-family-first map can remain a secondary figure or table.
- The working title's emphasis on “causal discovery” may overstate a small formal-discovery subset unless “discovery” is explicitly defined as a claim stratum rather than a prevalent study workflow.

### Recommended reconciliation

Do not discard the working synthesis. Use the six archetypes as the reader-facing Results spine and the synthesis's five-axis evidence map as the analytic framework underneath it. In short: **archetype first for comprehension; claim stratum and validation second for appraisal**.

## Full-text audit trail (38 reports)

The following deterministic Markdown files were directly inspected. “Evidence checked” names the sections used to verify the report's empirical logic.

| DOI | Short title/model | Format | Evidence checked |
|---|---|---|---|
| 10.1001/jamapsychiatry.2024.1429 | Psychiatric traits/smoking and longevity; human summary data | Article | Abstract; MR assumptions; statistical analysis; longevity results; limitations |
| 10.1002/advs.202514269 | FMT and age-related hearing loss; germ-free mice/cells | Article | Abstract; Results 2.2-2.9; study design; discussion/limitations |
| 10.1002/imo2.70128 | Uterus-weight mediation; aged hens | Article | Graphical Abstract; cohort description; statistical mediation; integration results |
| 10.1007/s11306-023-02022-w | SKN-1 metabolism and lifespan; *C. elegans* | Article | Abstract; omics methods; Results; Conclusion |
| 10.1016/j.celrep.2024.115099 | Glial Ugt35b and lifespan; *Drosophila* | Article | Summary; target/lipid results; rescue; limitations |
| 10.1016/j.celrep.2025.116795 | CD8 T-cell senescence; human cells | Article | Summary; cohort/state profiling; TF perturbation; Discussion |
| 10.1016/j.cels.2021.09.005 | Liver age-by-diet map; BXD mice/worm validation | Article | Summary; study design; Results; Discussion |
| 10.1016/j.devcel.2023.05.015 | APRT perturbation and lifespan; killifish | Article | Summary; CRISPR design; lifespan result; omics; limitations |
| 10.1016/j.exger.2025.112815 | Acupuncture and ovarian senescence; rats | Article | Introduction; randomization; omics methods; Results |
| 10.1016/j.psj.2026.107043 | Dietary supplement and ovarian function; hens | Article | Abstract; randomized feeding design; Results/discussion |
| 10.1038/s41392-026-02799-x | Bisphosphonate response; humans/mice/cells | Article | Abstract; trial synthesis; human proteomics; mouse spatial transcriptomics; cell dosing |
| 10.1038/s41438-020-00420-y | Temperature and pear-fruit senescence | Article | Abstract; experimental design; Results |
| 10.1038/s41467-023-37729-w | EAA/longevity multi-omic genetics; human | Article | Introduction; TWAS/MR Results; Discussion/limitations |
| 10.1038/s41467-024-46037-w | Pol I and healthy longevity; worms/human fibroblasts | Article | Abstract; genetic/pharmacological perturbations; lifespan/healthspan Results |
| 10.1038/s41536-026-00490-x | Senolytics and aged kidney; mice | Article | Abstract; treatment design; proteomics/single-cell Results |
| 10.1038/s41586-026-10524-5 | Sleep and 23 biological-age clocks; human | Article | Introduction; clock Results; sensitivity analyses; limitations |
| 10.1038/s43587-023-00451-9 | Youthful circulation/parabiosis; mice | Article | Abstract; attachment/detachment design; lifespan/clocks Results; caveats |
| 10.1038/s43587-026-01100-7 | lncRNA perturb-multiome; human cells/mouse lung | Article | Abstract; perturbation design/data availability |
| 10.1093/bib/bbag271 | StackAge; UK Biobank | Article | Abstract; cohort split; model architecture; mediation rationale |
| 10.1093/eurheartj/ehad361 | Atherosclerosis, EAA, inflammation; human | Article | Abstract methods/results; Conclusion; mediation statements |
| 10.1093/geroni/igad104.1942 | Youthful circulation; mice | Conference abstract | Abstract text and overlap with full article |
| 10.1093/plphys/kiaa034 | KLU, leaf longevity, drought; *Arabidopsis* | Article | Abstract; background; Results |
| 10.1101/2025.06.19.660635 | LATS1/2 and endothelial SAS; mice/human plaques | Preprint/abstract-only extraction | Preprint header; Abstract methods/results/conclusion |
| 10.1111/acel.13497 | Trans-omic MR of parental lifespan; human | Article | Abstract; TWAS/MR Results; PheWAS; limitations |
| 10.1111/acel.70064 | Aged microbiota and cognition; mice/human data | Article | Abstract; FMT Results; proteomics/metagenomics; limitations |
| 10.1111/acel.70103 | Therapeutic plasma exchange; human trial | Article | Abstract; CONSORT/design; clock/omics Results; limitations |
| 10.1111/acel.70498 | Losartan; aged mice and older men | Article | Abstract; animal design; human trial reuse; cross-species Results |
| 10.1128/msystems.01665-24 | IAA-AhR-Sirt2 and lifespan; flies | Article | Abstract; age microbiome map; supplementation/genetic Results |
| 10.1186/s12964-026-02985-y | CASP8 in OA; human cells/genetic data | Article | Abstract; triangulation study design; perturbation/genetic evidence; limitations |
| 10.1186/s12967-026-07766-2 | CXCL16+ macrophage senescence in LUAD | Article | Abstract; SMR/single-cell/spatial workflow; perturbation; limitations |
| 10.1186/s40364-023-00458-9 | FXR, diet, age, liver disease; mice | Article | Abstract; factorial Results; Discussion/limitations |
| 10.21037/tcr-2026-1-0264 | Cervical-cancer senescence predictor | Supplement only | All supplied supplementary legends; absence of main text |
| 10.26599/fshw.2026.9251125 | Cordycepin and lifespan; *C. elegans* | Article | Abstract; dosing/lifespan methods; multi-omics Results |
| 10.3389/fendo.2025.1661666 | Senescence genes and preeclampsia; human | Article | Abstract; study design; MR/SMR; expression follow-up |
| 10.3390/microorganisms13061379 | Exercise-microbiome-intestinal aging; mice | Article | Abstract; randomized exercise design; microbiome/metabolome Results |
| 10.4081/ejtm.2026.14960 | FES/training adaptation; rodents/humans | Conference collection | Proceedings index; full Abstract 009; time-course analytical methods |
| 10.64898/2026.07.09.736798 | HIV intestinal fucose-microbiome axis; human/organoid | Preprint | Abstract; human Results; organoid/fermentation experiments; limitations |
| 10.7554/elife.71624 | Transient reprogramming; human fibroblasts | Article | Abstract; reprogramming design; transcriptome/epigenome Results; methods |

## Bottom line

The real corpus is primarily a collection of **perturb-and-profile** studies, with smaller but coherent treatment, transfer/ecosystem, human-genetic, mapping, and clock/mediation niches. A Results section that starts with these empirical behaviors will let readers understand the field before asking how strong each causal claim is. Discovery/effect/validation should remain an essential claim-level appraisal framework, but it should not be the reader's first or only map of these 101 reports.
