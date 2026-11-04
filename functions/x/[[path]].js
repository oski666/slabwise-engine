// The data files of the API (D104) are not served directly.
export const onRequest = () => new Response("Not found", {status: 404});
