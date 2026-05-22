import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import DateRangePicker from "./DateRangePicker";
import { useFilters } from "../../store/filters";

// Reset Zustand store state between tests
beforeEach(() => {
  useFilters.setState({
    dateFrom: "2024-01-01",
    dateTo: "2024-01-31",
  });
});

describe("DateRangePicker", () => {
  it("renders preset buttons", () => {
    render(<DateRangePicker />);
    expect(screen.getByText("7д")).toBeInTheDocument();
    expect(screen.getByText("30д")).toBeInTheDocument();
    expect(screen.getByText("90д")).toBeInTheDocument();
  });

  it("renders date inputs with current filter values", () => {
    render(<DateRangePicker />);
    const inputs = screen.getAllByDisplayValue(/\d{4}-\d{2}-\d{2}/);
    expect(inputs).toHaveLength(2);
    expect(inputs[0]).toHaveValue("2024-01-01");
    expect(inputs[1]).toHaveValue("2024-01-31");
  });

  it("updates dateFrom on input change", () => {
    render(<DateRangePicker />);
    const [fromInput] = screen.getAllByDisplayValue(/\d{4}-\d{2}-\d{2}/);
    fireEvent.change(fromInput, { target: { value: "2024-02-01" } });
    expect(useFilters.getState().dateFrom).toBe("2024-02-01");
  });

  it("updates dateTo on input change", () => {
    render(<DateRangePicker />);
    const [, toInput] = screen.getAllByDisplayValue(/\d{4}-\d{2}-\d{2}/);
    fireEvent.change(toInput, { target: { value: "2024-02-28" } });
    expect(useFilters.getState().dateTo).toBe("2024-02-28");
  });

  it("preset buttons call setDateRange", () => {
    render(<DateRangePicker />);
    const btn7 = screen.getByText("7д");
    fireEvent.click(btn7);
    // After clicking 7д preset, dateTo should be today and dateFrom 7 days back
    const state = useFilters.getState();
    const today = new Date().toISOString().slice(0, 10);
    expect(state.dateTo).toBe(today);
    expect(state.dateFrom).not.toBe("2024-01-01");
  });
});
