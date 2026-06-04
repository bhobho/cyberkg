import axios from "axios";

const api = axios.create({ baseURL: "/api" });

export const fetchGraph        = ()           => api.get("/graph");
export const fetchStats        = ()           => api.get("/graph/stats");
export const fetchAttackPaths  = (asset)      => api.get("/attack-paths",        { params: { asset } });
export const fetchAllAssets    = ()           => api.get("/attack-paths/all-assets");
export const fetchVulnerability= (cve)        => api.get("/vulnerabilities",     { params: { cve } });
export const fetchCVEList      = ()           => api.get("/vulnerabilities/list");
export const fetchMalwareDetail= (name)       => api.get(`/vulnerabilities/malware/${encodeURIComponent(name)}`);
export const fetchMalwareList  = ()           => api.get("/vulnerabilities/malware");
