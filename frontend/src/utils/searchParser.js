export function parseSearchQuery(query) {
  const tokens = query.match(/(\w+:[^\s]+)|([^\s]+)/g);
  const parsed = {
    text: [],
    type: [],
    tag: [],
    status: [],
    scope: null,
  };
  if (tokens) {
    tokens.forEach((token) => {
      if (token.startsWith("type:")) {
        parsed.type.push(token.slice(5));
      } else if (token.startsWith("tag:")) {
        parsed.tag.push(token.slice(4));
      } else if (token.startsWith("status:")) {
        parsed.status.push(token.slice(7));
      } else if (token.startsWith("scope:")) {
        parsed.scope = token.slice(6);
      } else {
        parsed.text.push(token);
      }
    });
  }
  return parsed;
}

export function buildSearchParams(parsedQuery) {
  const params = {};
  if (parsedQuery.text && parsedQuery.text.length) {
    params.title = parsedQuery.text.join(" ");
  }
  if (parsedQuery.type && parsedQuery.type.length) {
    params.node_type = parsedQuery.type;
  }
  if (parsedQuery.status && parsedQuery.status.length) {
    params.status = parsedQuery.status;
  }
  if (parsedQuery.tag && parsedQuery.tag.length) {
    params.tags = parsedQuery.tag;
  }
  if (parsedQuery.scope) {
    params.scope = parsedQuery.scope;
  }
  return params;
}
