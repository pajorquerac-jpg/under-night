import { create } from "zustand";

import type { PlanDraft } from "@/types/api";

type PlanState = {
  drafts: PlanDraft[];
  addDraft: (draft: PlanDraft) => void;
};

export const usePlanStore = create<PlanState>((set) => ({
  drafts: [],
  addDraft: (draft) => set((state) => ({ drafts: [draft, ...state.drafts] })),
}));
