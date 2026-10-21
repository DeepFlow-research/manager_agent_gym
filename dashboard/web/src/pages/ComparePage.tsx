import { useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { api, type View } from "../api";
import { useAsync } from "../useAsync";
import ComparePanes from "../components/ComparePanes";

const VIEWS: View[] = ["workflow", "team", "preferences"];

export default function ComparePage() {
  const scenarios = useAsync(() => api.scenarios(), []);
  // View and scenarios live in the URL (?view=team&before=...&after=...) so a comparison is linkable.
  const [params, setParams] = useSearchParams();
  const view: View = VIEWS.includes(params.get("view") as View) ? (params.get("view") as View) : "workflow";
  const before = params.get("before") ?? "";
  const after = params.get("after") ?? "";
  const selected = params.get("node");
  const setParam = (key: string, value: string | null) =>
    setParams((p) => {
      const next = new URLSearchParams(p);
      if (value === null) next.delete(key);
      else next.set(key, value);
      if (key !== "node") next.delete("node"); // a new view or scenario clears the selection
      return next;
    }, { replace: true });

  const list = scenarios.data ?? [];

  // Default: the first team-variant scenario against its original of the same name.
  useEffect(() => {
    if (!list.length || before) return;
    const team = list.find((s) => s.collection === "specialist_loss");
    const base = team ?? list.find((s) => s.name === "legal_m_and_a") ?? list[0];
    const original = list.find((s) => s.collection === "end_to_end_examples" && s.name === base.name) ?? base;
    setParams(
      (p) => {
        const next = new URLSearchParams(p);
        next.set("before", original.id);
        next.set("after", base.id);
        return next;
      },
      { replace: true },
    );
  }, [list, before, setParams]);


  const data = useAsync(
    () => (before && after ? api.compare(view, before, after) : Promise.resolve(null)),
    [view, before, after],
  );

  const options = list.map((s) => (
    <option key={s.id} value={s.id}>
      {s.id}
    </option>
  ));

  return (
    <>
      <div className="filters">
        <div className="seg">
          {VIEWS.map((v) => (
            <button key={v} className={view === v ? "on" : ""} onClick={() => setParam("view", v)}>
              {v}
            </button>
          ))}
        </div>
        <label>
          Before
          <select value={before} onChange={(e) => setParam("before", e.target.value)}>
            {options}
          </select>
        </label>
        <label>
          After
          <select value={after} onChange={(e) => setParam("after", e.target.value)}>
            {options}
          </select>
        </label>
      </div>

      {scenarios.error && <div className="error">{scenarios.error}</div>}
      {data.error && <div className="error">{data.error}</div>}
      {data.data && (
        <ComparePanes data={data.data} beforeLabel={before} afterLabel={after} selected={selected} onSelect={(id) => setParam("node", id)} />
      )}
    </>
  );
}
