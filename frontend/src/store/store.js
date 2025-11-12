import create from 'zustand';

export const useStore = create((set) => ({
  markets: [],
  opportunities: [],
  selectedMarket: null,
  loading: false,
  error: null,

  setMarkets: (markets) => set({ markets }),
  setOpportunities: (opportunities) => set({ opportunities }),
  setSelectedMarket: (market) => set({ selectedMarket: market }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),

  fetchMarkets: async () => {
    set({ loading: true, error: null });
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL}/markets`);
      if (!response.ok) throw new Error('Failed to fetch markets');
      const data = await response.json();
      set({ markets: data });
    } catch (error) {
      set({ error: error.message });
    } finally {
      set({ loading: false });
    }
  },

  fetchOpportunities: async () => {
    set({ loading: true, error: null });
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL}/analysis/mispriced`);
      if (!response.ok) throw new Error('Failed to fetch opportunities');
      const data = await response.json();
      set({ opportunities: data.opportunities || [] });
    } catch (error) {
      set({ error: error.message });
    } finally {
      set({ loading: false });
    }
  },
}));
