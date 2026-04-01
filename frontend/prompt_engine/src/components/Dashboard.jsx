import { useEffect, useState } from "react";
import "../styles/Dashboard.css";
import { Plus, Mic } from "lucide-react";

export default function Dashboard() {
  const [inputValue, setInputValue] = useState("");
  const [selectedModel, setSelectedModel] = useState("Haiku 4.5");
  const [promptMode, setPromptMode] = useState("prompt_engineering");
  const [responseLength, setResponseLength] = useState("balanced");
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

  const navLinks = ["Product", "Agents", "Tech Stack", "Docs"];

  const agentFlowCards = [
    {
      title: "Intent Capture",
      text: "Understands your goal, constraints, and target output before generating anything.",
    },
    {
      title: "Agent Plan",
      text: "Creates an execution plan across prompt strategy, role setup, and context shaping.",
    },
    {
      title: "Precision Output",
      text: "Delivers clean prompts optimized for coding, writing, learning, and system design.",
    },
  ];

  const techStackCards = [
    {
      title: "Fast Frontend",
      text: "React + Vite interface with smooth transitions and low latency interactions.",
      tag: "UI",
    },
    {
      title: "Prompt Engine Core",
      text: "Python backend orchestrating model selection, response length, and mode controls.",
      tag: "Core",
    },
    {
      title: "Agent Modules",
      text: "Task-specific agents for prompt engineering, vibe coding, and workflow automation.",
      tag: "Agents",
    },
    {
      title: "Context Layer",
      text: "Memory-aware context that keeps user preferences and task intent consistent.",
      tag: "State",
    },
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
          prompt_mode: promptMode,
          response_length: responseLength,
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
      <div className="dashboard-content">
        <header className="top-nav" aria-label="Main navigation">
          <div className="brand-mark">PromptForge</div>

          <nav className="nav-links" aria-label="Primary">
            {navLinks.map((link) => (
              <a key={link} href="#" className="nav-link">
                {link}
              </a>
            ))}
          </nav>

          <button type="button" className="nav-cta">
            Start free
          </button>
        </header>

        <section className="main-section" id="hero">
          <div className="greeting-section">
            <h1 className="greeting-text">Build smarter prompts</h1>
            <p className="hero-subtext">
              Transform rough ideas into structured prompts with a focused AI
              workspace built for speed and clarity.
            </p>
          </div>

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

          <div className="generation-controls" aria-label="Generation controls">
            <label className="control-group" htmlFor="mode-selector">
              <span className="control-label">Mode</span>
              <select
                id="mode-selector"
                className="control-selector"
                value={promptMode}
                onChange={(e) => setPromptMode(e.target.value)}
              >
                <option value="prompt_engineering">Prompt Engineering</option>
                <option value="vibe_coding">Vibe Coding</option>
              </select>
            </label>

            <label className="control-group" htmlFor="length-selector">
              <span className="control-label">Length</span>
              <select
                id="length-selector"
                className="control-selector"
                value={responseLength}
                onChange={(e) => setResponseLength(e.target.value)}
              >
                <option value="short">Short</option>
                <option value="balanced">Balanced</option>
                <option value="long">Long</option>
              </select>
            </label>
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

          <div className="footer-hint">
            <p>
              Press <kbd>/</kbd> to see available commands
            </p>
          </div>
        </section>

        <section className="feature-sections" aria-label="Product capabilities">
          <div className="section-heading-wrap" id="agents">
            <p className="section-kicker">How Agents Work</p>
            <h2 className="section-heading">
              From idea to production-ready prompt
            </h2>
          </div>

          <div className="system-flow" aria-label="Agent flow cards">
            {agentFlowCards.map((card, index) => (
              <article
                key={card.title}
                className="system-card"
                style={{ animationDelay: `${160 + index * 120}ms` }}
              >
                <span className="system-step">0{index + 1}</span>
                <div>
                  <h3 className="system-title">{card.title}</h3>
                  <p className="system-text">{card.text}</p>
                </div>
              </article>
            ))}
          </div>

          <div className="section-heading-wrap system-heading" id="stack">
            <p className="section-kicker">Tech Stack</p>
            <h2 className="section-heading">
              Built for speed, precision, and scale
            </h2>
          </div>

          <div className="flashcard-grid">
            {techStackCards.map((card, index) => (
              <article
                key={card.title}
                className="flashcard"
                style={{ animationDelay: `${260 + index * 90}ms` }}
              >
                <span className="flashcard-tag">{card.tag}</span>
                <h3 className="flashcard-title">{card.title}</h3>
                <p className="flashcard-text">{card.text}</p>
              </article>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
