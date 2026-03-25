import { create } from 'zustand';

// 1. Define karein ke store mein kya kya hoga
interface CounterState {
  count: number;
  increment: () => void;
  decrement: () => void;
}

// 2. Store banayein
export const useCounterStore = create<CounterState>((set) => ({
  count: 0,
  increment: () => set((state) => ({ count: state.count + 1 })),
  decrement: () => set((state) => ({ count: state.count - 1 })),
}));