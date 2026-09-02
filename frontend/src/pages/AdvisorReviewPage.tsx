import { CheckCircle2, MessageSquareText, ShieldAlert, Send } from "lucide-react";
import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getAdvisorReview, submitAdvisorReviewComment } from "../api/innovationExtensionApi";
import type { AdvisorShare } from "../types/innovationExtension";

export function AdvisorReviewPage() {
  const { shareToken = "" } = useParams();
  const [review, setReview] = useState<AdvisorShare | null>(null);
  const [comment, setComment] = useState("This evidence appears relevant, but any stronger claim should remain user-confirmed.");
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");

  async function refresh() {
    setError("");
    const data = await getAdvisorReview(shareToken);
    setReview(data);
  }

  useEffect(() => {
    refresh().catch(() => setError("This adviser review link is invalid, expired, revoked, or has reached its access limit."));
  }, [shareToken]);

  async function submitComment() {
    await submitAdvisorReviewComment(shareToken, {
      suggestion_type: "Evidence review",
      target_type: "Evidence Passport",
      comment_text: comment,
      evidence_validation: "Partially supports",
    });
    setStatus("Comment submitted. The user must accept it before it affects any decision.");
    await refresh();
  }

  return (
    <main className="advisor-review-page">
      <section className="advisor-review-shell">
        <header>
          <p className="innovation-eyebrow">OrganicAI Compass shared review</p>
          <h1>{review?.purpose || "Advisor review"}</h1>
          <p>This shared review does not grant access to your full OrganicAI Compass account.</p>
        </header>

        {(status || error) ? (
          <div className="innovation-notices" aria-live="polite">
            {status ? <p><CheckCircle2 size={16} /> {status}</p> : null}
            {error ? <p className="innovation-notice-error"><ShieldAlert size={16} /> {error}</p> : null}
          </div>
        ) : null}

        {review ? (
          <div className="innovation-grid innovation-grid--main">
            <section className="innovation-panel">
              <header className="innovation-panel__header">
                <div>
                  <span className="innovation-panel__icon"><ShieldAlert size={20} /></span>
                  <h2>Selected Sections</h2>
                </div>
              </header>
              <div className="innovation-list">
                {(review.sections || []).map((section) => (
                  <article className="innovation-row" key={section.name}>
                    <div>
                      <b>{section.name}</b>
                      <p>{section.items.length} shared item(s)</p>
                      {section.limitations?.length ? <small>{section.limitations.join(" ")}</small> : null}
                    </div>
                  </article>
                ))}
              </div>
            </section>

            <section className="innovation-panel">
              <header className="innovation-panel__header">
                <div>
                  <span className="innovation-panel__icon"><MessageSquareText size={20} /></span>
                  <h2>Submit Review</h2>
                </div>
              </header>
              <label className="innovation-textarea-label">
                Comment
                <textarea value={comment} onChange={(event) => setComment(event.target.value)} />
              </label>
              <button className="organic-button" type="button" onClick={submitComment}>
                <Send size={16} /> Submit review
              </button>
              <div className="innovation-list">
                {review.comments.map((item) => (
                  <article className="innovation-row" key={item.id}>
                    <div>
                      <b>{item.suggestion_type}</b>
                      <p>{item.comment_text}</p>
                      <small>{item.status} - {item.evidence_validation}</small>
                    </div>
                  </article>
                ))}
              </div>
            </section>
          </div>
        ) : null}
      </section>
    </main>
  );
}
