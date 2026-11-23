import { useCallback, useEffect, useState } from 'react';
import { api, type Camera, type DetectionEvent, type Tracklet, type TrafficAggregate } from './api';

interface DashboardData {
  cameras: Camera[];
  tracklets: Tracklet[];
  events: DetectionEvent[];
  traffic: TrafficAggregate[];
}

const EMPTY_DATA: DashboardData = {
  cameras: [],
  tracklets: [],
  events: [],
  traffic: [],
};

export function useDashboardData() {
  const [data, setData] = useState<DashboardData>(EMPTY_DATA);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    const [cameras, tracklets, events, traffic] = await Promise.all([
      api.cameras(),
      api.tracklets(20),
      api.events(20),
      api.traffic(),
    ]);
    setData({ cameras, tracklets, events, traffic });
    setLoading(false);
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { ...data, loading, refresh };
}
