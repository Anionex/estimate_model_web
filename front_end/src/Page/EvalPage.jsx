import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import ApiUtill from "../ApiUtill";
import "../App.css";
import {
  Card,
  CardHeader,
  CardBody,
  Button,
  Textarea,
  Input,
  Tabs,
  Tab,
  Chip,
  CheckboxGroup,
  Checkbox,
  Divider,
  Accordion,
  AccordionItem,
} from "@nextui-org/react";
import { CircularProgress } from "@nextui-org/react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const POLL_INTERVAL = 3000;

function scoreColor(score) {
  if (score >= 8) return "success";
  if (score >= 5) return "warning";
  return "danger";
}

function EvalPage() {
  // Shared state
  const [dimensions, setDimensions] = useState([]);
  const [selectedDims, setSelectedDims] = useState([]);
  const scorePollRef = useRef(null);
  const comparePollRef = useRef(null);

  // Score tab state
  const [scoreLoading, setScoreLoading] = useState(false);
  const [scoreRequest, setScoreRequest] = useState("");
  const [scoreItineraries, setScoreItineraries] = useState([
    { id: "model-A", itinerary: "" },
  ]);
  const [scoreResults, setScoreResults] = useState(null);

  // Compare tab state
  const [compareLoading, setCompareLoading] = useState(false);
  const [compareRequest, setCompareRequest] = useState("");
  const [compareItineraries, setCompareItineraries] = useState([
    { id: "model-A", itinerary: "" },
    { id: "model-B", itinerary: "" },
  ]);
  const [compareResults, setCompareResults] = useState(null);

  // Fetch dimensions on mount
  useEffect(() => {
    axios
      .get(ApiUtill.url_root + ApiUtill.url_eval_dimensions)
      .then((res) => {
        const dims = res.data.dimensions || [];
        setDimensions(dims);
        setSelectedDims(dims.map((d) => d.name));
      })
      .catch((err) => console.error("Failed to fetch dimensions:", err));

    return () => {
      if (scorePollRef.current) clearInterval(scorePollRef.current);
      if (comparePollRef.current) clearInterval(comparePollRef.current);
    };
  }, []);

  // ============ Poll Helper ============
  function pollTaskStatus(pollRef, taskId, onComplete, onError) {
    pollRef.current = setInterval(async () => {
      try {
        const res = await axios.get(
          ApiUtill.url_root + ApiUtill.url_task_status + "/" + taskId
        );
        const data = res.data;
        if (data.status === "completed") {
          clearInterval(pollRef.current);
          pollRef.current = null;
          onComplete(data.result);
        } else if (data.status === "failed") {
          clearInterval(pollRef.current);
          pollRef.current = null;
          onError(data.error || "Task failed");
        }
      } catch (err) {
        clearInterval(pollRef.current);
        pollRef.current = null;
        onError(err.message);
      }
    }, POLL_INTERVAL);
  }

  // ============ Score Tab Handlers ============
  function addScoreItinerary() {
    const idx = scoreItineraries.length + 1;
    setScoreItineraries([
      ...scoreItineraries,
      { id: `model-${String.fromCharCode(64 + idx)}`, itinerary: "" },
    ]);
  }

  function removeScoreItinerary(index) {
    if (scoreItineraries.length <= 1) return;
    setScoreItineraries(scoreItineraries.filter((_, i) => i !== index));
  }

  function updateScoreItinerary(index, field, value) {
    const updated = [...scoreItineraries];
    updated[index] = { ...updated[index], [field]: value };
    setScoreItineraries(updated);
  }

  async function runScore() {
    setScoreLoading(true);
    setScoreResults(null);
    try {
      const payload = {
        itineraries: scoreItineraries.map((it) => ({
          id: it.id,
          user_request: scoreRequest,
          itinerary: it.itinerary,
          metadata: {},
        })),
        dimensions: selectedDims,
      };
      const res = await axios.post(
        ApiUtill.url_root + ApiUtill.url_eval_score,
        payload
      );
      const taskId = res.data.task_id;
      pollTaskStatus(
        scorePollRef,
        taskId,
        (result) => {
          setScoreResults(result);
          setScoreLoading(false);
        },
        (error) => {
          alert("Evaluation failed: " + error);
          setScoreLoading(false);
        }
      );
    } catch (err) {
      alert("Failed to submit: " + err.message);
      setScoreLoading(false);
    }
  }

  // ============ Compare Tab Handlers ============
  function addCompareItinerary() {
    const idx = compareItineraries.length + 1;
    setCompareItineraries([
      ...compareItineraries,
      { id: `model-${String.fromCharCode(64 + idx)}`, itinerary: "" },
    ]);
  }

  function removeCompareItinerary(index) {
    if (compareItineraries.length <= 2) return;
    setCompareItineraries(compareItineraries.filter((_, i) => i !== index));
  }

  function updateCompareItinerary(index, field, value) {
    const updated = [...compareItineraries];
    updated[index] = { ...updated[index], [field]: value };
    setCompareItineraries(updated);
  }

  async function runCompare() {
    setCompareLoading(true);
    setCompareResults(null);
    try {
      const payload = {
        user_request: compareRequest,
        itineraries: compareItineraries.map((it) => ({
          id: it.id,
          itinerary: it.itinerary,
          metadata: {},
        })),
        dimensions: selectedDims,
      };
      const res = await axios.post(
        ApiUtill.url_root + ApiUtill.url_eval_compare,
        payload
      );
      const taskId = res.data.task_id;
      pollTaskStatus(
        comparePollRef,
        taskId,
        (result) => {
          setCompareResults(result);
          setCompareLoading(false);
        },
        (error) => {
          alert("Comparison failed: " + error);
          setCompareLoading(false);
        }
      );
    } catch (err) {
      alert("Failed to submit: " + err.message);
      setCompareLoading(false);
    }
  }

  // ============ Render Helpers ============
  function renderItineraryInputs(items, updateFn, removeFn, addFn, minCount) {
    return (
      <div className="flex flex-col gap-3 w-full">
        {items.map((item, index) => (
          <Card key={index} className="w-full">
            <CardBody className="gap-3">
              <div className="flex gap-2 items-center">
                <Input
                  label="ID / Label"
                  value={item.id}
                  onChange={(e) => updateFn(index, "id", e.target.value)}
                  className="max-w-[200px]"
                  size="sm"
                />
                {items.length > minCount && (
                  <Button
                    color="danger"
                    variant="flat"
                    size="sm"
                    onPress={() => removeFn(index)}
                  >
                    Remove
                  </Button>
                )}
              </div>
              <Textarea
                label="Itinerary"
                placeholder="Paste the itinerary text here..."
                value={item.itinerary}
                onChange={(e) => updateFn(index, "itinerary", e.target.value)}
                minRows={4}
                maxRows={12}
              />
            </CardBody>
          </Card>
        ))}
        <Button color="primary" variant="flat" onPress={addFn} className="w-fit">
          + Add Itinerary
        </Button>
      </div>
    );
  }

  function renderDimensionSelector() {
    return (
      <div className="w-full">
        <p className="text-sm text-default-500 mb-2">Evaluation Dimensions</p>
        <CheckboxGroup
          orientation="horizontal"
          value={selectedDims}
          onChange={setSelectedDims}
        >
          {dimensions.map((dim) => (
            <Checkbox key={dim.name} value={dim.name} size="sm">
              {dim.name.replace(/_/g, " ")}
            </Checkbox>
          ))}
        </CheckboxGroup>
      </div>
    );
  }

  function renderScoreResults() {
    if (!scoreResults) return null;
    const evaluations = scoreResults.evaluations || [];
    return (
      <div className="flex flex-col gap-4 w-full mt-4">
        <h3 className="text-xl font-bold">Results</h3>
        {evaluations.map((evalItem) => (
          <Card key={evalItem.input_id} className="w-full">
            <CardHeader className="flex justify-between">
              <span className="font-bold text-lg">{evalItem.input_id}</span>
              <Chip color={scoreColor(evalItem.aggregate_score)} size="lg" variant="flat">
                Avg: {evalItem.aggregate_score}/10
              </Chip>
            </CardHeader>
            <CardBody>
              <div className="flex flex-col gap-2">
                {evalItem.scores.map((s) => (
                  <div key={s.dimension} className="flex flex-col gap-1">
                    <div className="flex items-center gap-2">
                      <Chip color={scoreColor(s.score)} size="sm" variant="flat">
                        {s.score}/10
                      </Chip>
                      <span className="font-medium">
                        {s.dimension.replace(/_/g, " ")}
                      </span>
                    </div>
                    <p className="text-sm text-default-500 ml-8">
                      {s.justification}
                    </p>
                  </div>
                ))}
              </div>
            </CardBody>
          </Card>
        ))}
      </div>
    );
  }

  function renderCompareResults() {
    if (!compareResults) return null;
    const { pairwise_results, rankings, overall_ranking } = compareResults;
    return (
      <div className="flex flex-col gap-4 w-full mt-4">
        <h3 className="text-xl font-bold">Results</h3>

        {/* Overall ranking */}
        <Card className="w-full">
          <CardHeader>
            <span className="font-bold text-lg">Overall Ranking</span>
          </CardHeader>
          <CardBody>
            <div className="flex gap-2 items-center flex-wrap">
              {overall_ranking.map((id, idx) => (
                <React.Fragment key={id}>
                  <Chip
                    color={idx === 0 ? "success" : idx === 1 ? "warning" : "default"}
                    variant="flat"
                    size="lg"
                  >
                    #{idx + 1} {id}
                  </Chip>
                  {idx < overall_ranking.length - 1 && (
                    <span className="text-default-400">&gt;</span>
                  )}
                </React.Fragment>
              ))}
            </div>
          </CardBody>
        </Card>

        {/* Per-dimension rankings */}
        <Card className="w-full">
          <CardHeader>
            <span className="font-bold text-lg">Per-Dimension Rankings</span>
          </CardHeader>
          <CardBody>
            <div className="flex flex-col gap-2">
              {Object.entries(rankings || {}).map(([dim, ranking]) => (
                <div key={dim} className="flex items-center gap-2">
                  <span className="font-medium min-w-[180px]">
                    {dim.replace(/_/g, " ")}:
                  </span>
                  <span>{ranking.join(" > ")}</span>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>

        {/* Pairwise details */}
        <Card className="w-full">
          <CardHeader>
            <span className="font-bold text-lg">Pairwise Details</span>
          </CardHeader>
          <CardBody>
            <Accordion>
              {pairwise_results.map((pr, idx) => {
                const winnerDisplay =
                  pr.winner === "tie"
                    ? "Tie"
                    : pr.winner === "A"
                    ? pr.itinerary_a_id
                    : pr.itinerary_b_id;
                return (
                  <AccordionItem
                    key={idx}
                    title={
                      <span>
                        <strong>{pr.dimension.replace(/_/g, " ")}</strong>
                        {" | "}
                        {pr.itinerary_a_id} vs {pr.itinerary_b_id}
                        {" -> "}
                        <Chip
                          size="sm"
                          color={pr.winner === "tie" ? "default" : "primary"}
                          variant="flat"
                        >
                          {winnerDisplay}
                        </Chip>
                      </span>
                    }
                  >
                    <p className="text-sm text-default-500">
                      {pr.justification}
                    </p>
                  </AccordionItem>
                );
              })}
            </Accordion>
          </CardBody>
        </Card>
      </div>
    );
  }

  // ============ Main Render ============
  return (
    <div className="App">
      <h1 className="text-2xl font-bold mb-6">Itinerary Evaluation</h1>

      <Tabs aria-label="Evaluation mode" className="mb-6" size="lg">
        {/* ====== Score Tab ====== */}
        <Tab key="score" title="Score">
          <div className="flex flex-col gap-4 items-start">
            <Textarea
              label="User Request"
              placeholder="Enter the original travel query..."
              value={scoreRequest}
              onChange={(e) => setScoreRequest(e.target.value)}
              minRows={2}
              className="w-full"
            />

            {renderDimensionSelector()}

            <Divider />

            <h3 className="text-lg font-semibold">Itineraries</h3>
            {renderItineraryInputs(
              scoreItineraries,
              updateScoreItinerary,
              removeScoreItinerary,
              addScoreItinerary,
              1
            )}

            <Button
              color="primary"
              onPress={runScore}
              isDisabled={
                scoreLoading ||
                !scoreRequest.trim() ||
                scoreItineraries.some((it) => !it.itinerary.trim()) ||
                selectedDims.length === 0
              }
              size="lg"
              className="mt-2"
            >
              {scoreLoading ? (
                <>
                  <CircularProgress size="sm" className="mr-2" /> Evaluating...
                </>
              ) : (
                "Run Evaluation"
              )}
            </Button>

            {renderScoreResults()}
          </div>
        </Tab>

        {/* ====== Compare Tab ====== */}
        <Tab key="compare" title="A/B Compare">
          <div className="flex flex-col gap-4 items-start">
            <Textarea
              label="User Request"
              placeholder="Enter the shared travel query for comparison..."
              value={compareRequest}
              onChange={(e) => setCompareRequest(e.target.value)}
              minRows={2}
              className="w-full"
            />

            {renderDimensionSelector()}

            <Divider />

            <h3 className="text-lg font-semibold">Itineraries to Compare</h3>
            {renderItineraryInputs(
              compareItineraries,
              updateCompareItinerary,
              removeCompareItinerary,
              addCompareItinerary,
              2
            )}

            <Button
              color="primary"
              onPress={runCompare}
              isDisabled={
                compareLoading ||
                !compareRequest.trim() ||
                compareItineraries.some((it) => !it.itinerary.trim()) ||
                selectedDims.length === 0
              }
              size="lg"
              className="mt-2"
            >
              {compareLoading ? (
                <>
                  <CircularProgress size="sm" className="mr-2" /> Comparing...
                </>
              ) : (
                "Run Comparison"
              )}
            </Button>

            {renderCompareResults()}
          </div>
        </Tab>
      </Tabs>
    </div>
  );
}

export default EvalPage;
