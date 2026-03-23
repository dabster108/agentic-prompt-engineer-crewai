import { useEffect, useState } from "react";
import "../styles/Dashboard.css";
import { Sparkles, Plus, Mic } from "lucide-react";

export default function Dashboard() {
  const [inputValue, setInputValue] = useState("");
  const [selectedModel, setSelectedModel] = useState("Haiku 4.5");
  const [generatedPrompt, setGeneratedPrompt] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [activeStepIndex, setActiveStepIndex] = useState(0);
  const [loadingDots, setLoadingDots] = useState("");

  const loadingSteps = [
    { short: "Start", detail: "Task started" },
    { short: "Engine", detail: "Executing prompt engine" },
    { short: "Finish", detail: "Finalizing answer" },
  ];

  const actionButtons = [
    { label: "Write" },
    { label: "Learn" },
    { label: "Code" },
    { label: "Life stuff" },
    { label: "Claude's choice" },
  ];

  const handleInputFocus = (e) => {
    e.target.parentElement.classList.add("focused");
  };

  const handleInputBlur = (e) => {
    e.target.parentElement.classList.remove("focused");
  };

  useEffect(() => {
    if (!isLoading) {
      setLoadingDots("");
      setActiveStepIndex(0);
      return;
    }

    const stepInterval = setInterval(() => {
      setActiveStepIndex((current) =>
        current < loadingSteps.length - 1 ? current + 1 : current,
      );
    }, 1300);

    const dotsInterval = setInterval(() => {
      setLoadingDots((current) => (current.length >= 3 ? "" : `${current}.`));
    }, 350);

    return () => {
      clearInterval(stepInterval);
      clearInterval(dotsInterval);
    };
  }, [isLoading, loadingSteps.length]);

  const generatePrompt = async () => {
    const trimmedInput = inputValue.trim();
    if (!trimmedInput) {
      setErrorMessage("Type something first so I can generate a prompt.");
      setGeneratedPrompt("");
      return;
    }

    setIsLoading(true);
    setErrorMessage("");

    try {
      const response = await fetch("/api/prompt", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_input: trimmedInput,
          model: selectedModel,
        }),
      });

      if (!response.ok) {
        throw new Error("Could not generate prompt right now.");
      }

      const data = await response.json();
      setGeneratedPrompt(data.prompt || "");
    } catch (error) {
      setGeneratedPrompt("");
      setErrorMessage(error.message || "Something went wrong.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputKeyDown = (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      generatePrompt();
    }
  };

  return (
    <div className="dashboard-container">
      {/* Soft gradient background */}
      <div className="background-gradient"></div>

      <div className="dashboard-content">
        {/* Main Content Section */}
        <div className="main-section">
          {/* Greeting */}
          <div className="greeting-section">
            <h1 className="greeting-text">
              <span className="greeting-icon" aria-hidden="true">
                <Sparkles size={24} />
              </span>
              Afternoon, Dikshanta
            </h1>
            <p className="context-highlight">Turn your context into prompt</p>
          </div>

          {/* Input Box */}
          <div className="input-wrapper">
            <div className="input-container">
              <button
                className="input-icon input-icon-left"
                aria-label="Add new"
              >
                <Plus size={20} />
              </button>

              <input
                type="text"
                className="main-input"
                placeholder="Type / for skills"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleInputKeyDown}
                onFocus={handleInputFocus}
                onBlur={handleInputBlur}
              />

              <div className="input-icons-right">
                <select
                  className="model-selector"
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                >
                  <option>Haiku 4.5</option>
                  <option>Sonnet 4.5</option>
                  <option>Opus 4.1</option>
                </select>

                <button
                  className="input-icon mic-button"
                  aria-label="Voice input"
                >
                  <Mic size={20} />
                </button>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="action-buttons">
            {actionButtons.map((btn) => (
              <button
                key={btn.label}
                className="action-btn"
                type="button"
                onClick={btn.label === "Write" ? generatePrompt : undefined}
              >
                <span className="btn-label">{btn.label}</span>
              </button>
            ))}
          </div>

          {(isLoading || errorMessage || generatedPrompt) && (
            <div className="result-panel" aria-live="polite">
              {isLoading && (
                <div
                  className="execution-state"
                  role="status"
                  aria-live="polite"
                >
                  <div className="execution-loader" aria-hidden="true">
                    <span className="loader-ring" />
                    <span className="loader-core" />
                    <span className="loader-orbit-dot" />
                  </div>

                  <div className="execution-text">
                    <p className="result-loading-title">Generating prompt</p>
                    <p className="result-loading-subtitle">
                      {loadingSteps[activeStepIndex].detail}
                      {loadingDots}
                    </p>
                    <div className="execution-steps" aria-hidden="true">
                      {loadingSteps.map((step, index) => {
                        const stepState =
                          index < activeStepIndex
                            ? "done"
                            : index === activeStepIndex
                              ? "active"
                              : "pending";

                        return (
                          <div className="execution-step-item" key={step.short}>
                            <div
                              className={`execution-step execution-step-${stepState}`}
                            >
                              <span className="execution-step-dot" />
                              <span className="execution-step-label">
                                {step.short}
                              </span>
                            </div>
                            {index < loadingSteps.length - 1 && (
                              <span
                                className={`execution-step-connector execution-step-connector-${stepState}`}
                              />
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              )}
              {errorMessage && <p className="result-error">{errorMessage}</p>}
              {generatedPrompt && (
                <>
                  <p className="result-title">Generated Prompt</p>
                  <pre className="result-content">{generatedPrompt}</pre>
                </>
              )}
            </div>
          )}

          {/* Footer hint */}
          <div className="footer-hint">
            <p>
              Press <kbd>/</kbd> to see available commands
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
