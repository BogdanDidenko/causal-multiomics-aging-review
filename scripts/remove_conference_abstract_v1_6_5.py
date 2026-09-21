"""Move the user-rejected conference abstract out of full-text assessment."""
import csv
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PREVIOUS=ROOT/"analysis/full_text_screening/prisma_slice_v1.6.4_source_age_correction"
OUT=ROOT/"analysis/full_text_screening/prisma_slice_v1.6.5_no_conference_abstract"
TARGET="doi:10.1210/jendso/bvae163.582"

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n")

def main():
    if OUT.exists():raise ValueError("Refuse to overwrite conference-abstract correction")
    old=list(csv.DictReader((PREVIOUS/"eligibility_ledger_295.csv").open()))
    target=next(r for r in old if r["record_id"]==TARGET)
    assert target["final_decision"]=="manual_review"
    rows=[r for r in old if r["record_id"]!=TARGET]
    assert len(rows)==294 and all(r["final_decision"] in {"assessed","exclude"} for r in rows)
    assert sum(r["final_decision"]=="assessed" for r in rows)==280
    assert sum(r["final_decision"]=="exclude" for r in rows)==14
    dispositions=list(csv.DictReader((PREVIOUS/"report_disposition_359.csv").open()))
    for row in dispositions:
        if row["record_id"]==TARGET:
            row["prisma_disposition"]="nonarticle_conference_abstract_object"
            row["reason"]="User decision: conference abstract only; do not include in full-text eligibility cohort."
    assert len(dispositions)==359 and sum(r["prisma_disposition"]=="nonarticle_conference_abstract_object" for r in dispositions)==1
    OUT.mkdir(parents=True)
    with (OUT/"eligibility_ledger_294.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    with (OUT/"report_disposition_359.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(dispositions[0]));w.writeheader();w.writerows(dispositions)
    decision={"record_id":TARGET,"doi":target["doi"],"title":target["title"],
              "previous_disposition":"eligibility_unresolved",
              "new_disposition":"nonarticle_conference_abstract_object",
              "decision_source":"user","decision_date":"2026-09-20",
              "reason":"Conference abstract only; exclude from full-text report cohort.",
              "scientific_exclusion_code":None}
    write(OUT/"conference_abstract_decision.json",decision)
    flow={"scope":"stable_layer_pair_extension_only","status":"full_text_eligibility_complete_for_294_screened_reports_three_deferred",
          "canonical_records":359,"nonarticle_objects":25,"reports_not_retrieved":37,
          "retrieved_full_reports":297,"separately_deferred_reports":3,"screened_full_reports":294,
          "reports_meeting_full_text_eligibility":280,"reports_excluded":14,"reports_unresolved":0,
          "conference_abstracts_removed_from_full_text_cohort":1,
          "human_adjudications_added":1,"whole_review_prisma_closed":False,
          "balances":{"canonical":359==25+37+297,"retrieved":297==3+294,"screened":294==280+14}}
    write(OUT/"prisma_flow.json",flow)
    (OUT/"README.md").write_text(
      "# Conference-abstract correction v1.6.5\n\n"
      "The user classified `10.1210/jendso/bvae163.582` as a conference-abstract-only object and instructed that it not be added to the full-text cohort. "
      "It is retained in the 359-record disposition ledger as `nonarticle_conference_abstract_object`; it is not a scientific full-text exclusion and carries no EC code.\n\n"
      "The stable-layer-pair extension now contains 25 nonarticle objects, 37 reports not retrieved, and 297 retrieved full reports. "
      "Of the retrieved full reports, 294 were screened and 3 remain separately deferred. The screened flow has 280 eligible reports, 14 exclusions, and 0 unresolved. "
      "Whole-review PRISMA remains open because the prior cohort, deferred reports, other upstream queues, and report-to-study linkage remain separate.\n")
    sources=[PREVIOUS/"eligibility_ledger_295.csv",PREVIOUS/"report_disposition_359.csv",Path(__file__)]
    write(OUT/"audit_manifest.json",{"sources":[{"path":str(p.relative_to(ROOT)),"sha256":sha(p)} for p in sources],
                                     "outputs":[{"path":str(p.relative_to(ROOT)),"sha256":sha(p)} for p in sorted(OUT.rglob("*")) if p.is_file()],
                                     "checks":flow["balances"]})
    print(json.dumps(flow,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
