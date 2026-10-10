# Read-only research tool contracts

RIL-046 defines bounded tools for races, histories, features, markets, forecasts, backtests, and provenance. Every request requires a timezone-aware `as_of` instant, an authenticated user ID, an explicit limit of 1–100, and tool arguments. Every response is marked read-only and returns no more than the requested limit.

Tool execution requires the scope mapped to that tool. Missing scopes return `NOT_ENTITLED`; an unregistered capability returns `NOT_AVAILABLE`; neither returns fabricated rows. Handlers receive the exact `as_of`, limit, and arguments and cannot bypass the response bound.

The fixture is synthetic and offline. It demonstrates the catalog, an authorized bounded read, and a denied market request. These contracts do not create write tools, external network access, wagering, or order execution.
