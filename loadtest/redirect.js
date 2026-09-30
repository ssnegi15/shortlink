import http from "k6/http";
import { check } from "k6";

export const options = {
  scenarios: {
    peak: {
      executor: "constant-arrival-rate",
      rate: 5000,
      timeUnit: "1s",
      duration: "2m",
      preAllocatedVUs: 250,
      maxVUs: 1000
    }
  },
  thresholds: {
    http_req_failed: ["rate<0.01"],
    http_req_duration: ["p(95)<100", "p(99)<250"]
  }
};

const BASE_URL = __ENV.BASE_URL || "http://localhost:8080";
const CODE = __ENV.CODE || "aZ91kLm2Pq7X";

export default function () {
  const response = http.get(`${BASE_URL}/${CODE}`, {
    redirects: 0,
    tags: { endpoint: "redirect" }
  });

  check(response, {
    "redirect returns 302": (r) => r.status === 302
  });
}
