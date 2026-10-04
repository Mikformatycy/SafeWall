// Change to 'api' when the verified Pi collector is available on the same origin.
// The live adapter never substitutes demo readings after a failed request.
export const dashboardConfig = Object.freeze({ dataSource: 'mock', pollIntervalMs: 5000 });
