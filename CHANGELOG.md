# CHANGELOG


## v0.3.0 (2025-05-23)

### Features

- Support to task status notification for long running requests
  ([#145](https://github.com/bsantanna/agent-lab/pull/145),
  [`1a877f8`](https://github.com/bsantanna/agent-lab/commit/1a877f82b31d63597b3bbad1a88a1b48e7e73a01))

* feat: redis application setup

* feat: task notification service on top of redis pub sub

* feat: task notification service for browser tool call

* feat: refactors supervised workflow base class, decouples chain methods

* feat: notification service calls for voice memos agent

* feat: notification service calls for general agent

* feat: notification service calls for vision document and adaptive rag agents

* feat: notification service calls for agreement planner

* feat: websocket endpoint subscribing to redis channel

* feat: updates depdendencies

* fix: linting error on log message

* fix: return types adjust


## v0.2.14 (2025-05-18)

### Bug Fixes

- Adjusts image sign command ([#139](https://github.com/bsantanna/agent-lab/pull/139),
  [`8bfce75`](https://github.com/bsantanna/agent-lab/commit/8bfce754b10cce6e4ec08ff2be8bf20c468a2d9a))


## v0.2.13 (2025-05-18)

### Bug Fixes

- Adjusts image sign command (7) ([#138](https://github.com/bsantanna/agent-lab/pull/138),
  [`89d7019`](https://github.com/bsantanna/agent-lab/commit/89d7019679f4d79cfabd77973a74979cefa9ba40))


## v0.2.12 (2025-05-18)

### Bug Fixes

- Fix/release 2 adjusts docker image auditing 6
  ([#137](https://github.com/bsantanna/agent-lab/pull/137),
  [`b6f15ee`](https://github.com/bsantanna/agent-lab/commit/b6f15ee8ef59ea5072c8ae683570b596a673287c))

* fix: adjusts image sign command (6)

* fix: adjust build pipeline, avoid extra build


## v0.2.11 (2025-05-18)

### Bug Fixes

- Adjusts image sign command (5) ([#136](https://github.com/bsantanna/agent-lab/pull/136),
  [`40ce3f4`](https://github.com/bsantanna/agent-lab/commit/40ce3f493295bbdefd21c1fc4971007e624f7d31))


## v0.2.10 (2025-05-18)

### Bug Fixes

- Adjusts image sign command (4) ([#135](https://github.com/bsantanna/agent-lab/pull/135),
  [`92f511d`](https://github.com/bsantanna/agent-lab/commit/92f511dc74ed0089227adb2aec4307a17c52f9a5))


## v0.2.9 (2025-05-18)

### Bug Fixes

- Adjusts image sign command (3) ([#134](https://github.com/bsantanna/agent-lab/pull/134),
  [`517c532`](https://github.com/bsantanna/agent-lab/commit/517c532e54284afe0317d081bc2a18e3c2df34e4))


## v0.2.8 (2025-05-18)

### Bug Fixes

- Adjusts image sign command (2) ([#133](https://github.com/bsantanna/agent-lab/pull/133),
  [`dafb6a2`](https://github.com/bsantanna/agent-lab/commit/dafb6a2e53a3be0b4256999f67bd61151bbfed3b))


## v0.2.7 (2025-05-18)

### Bug Fixes

- Adjusts image sign command ([#132](https://github.com/bsantanna/agent-lab/pull/132),
  [`8438aa0`](https://github.com/bsantanna/agent-lab/commit/8438aa06aa9734bbf6f676415a3e95369cfad6f5))


## v0.2.6 (2025-05-18)

### Bug Fixes

- Using headless browser ([#131](https://github.com/bsantanna/agent-lab/pull/131),
  [`e3f234a`](https://github.com/bsantanna/agent-lab/commit/e3f234a9bd10fd1b9afa10dda6500c7c984de0d2))

- Using xvfb wrapper for headless browser, adjusts cosign
  ([#130](https://github.com/bsantanna/agent-lab/pull/130),
  [`0b97cc5`](https://github.com/bsantanna/agent-lab/commit/0b97cc54e3c41df1bbff1bf436a2f9c3f206e056))


## v0.2.5 (2025-05-18)

### Bug Fixes

- Docker image auditing and python code refactoring
  ([#129](https://github.com/bsantanna/agent-lab/pull/129),
  [`0d83670`](https://github.com/bsantanna/agent-lab/commit/0d836706c6009244419be94f5093745ad7580c86))


## v0.2.4 (2025-05-17)

### Bug Fixes

- Adjusts dependencies and vulnerabilities on Docker base image, upgrades browser-use
  ([#128](https://github.com/bsantanna/agent-lab/pull/128),
  [`ecdb178`](https://github.com/bsantanna/agent-lab/commit/ecdb1781146d7b86131c02140cb6311f245f3365))

* fix: upgrades libs and dockerfile

* fix: adjusts dependencies versions

* fix: adjusts CI pipelines

* fix: adjusts chromium install command

* fix: rollback adjusts chromium install command

* fix: adjusts COPY command scope in dockerfile

* fix: adjusts COPY command scope in dockerfile, adjusts browser-use tool call


## v0.2.3 (2025-05-16)

### Bug Fixes

- Adjusts in system prompts to align with business requirements
  ([#127](https://github.com/bsantanna/agent-lab/pull/127),
  [`fda2290`](https://github.com/bsantanna/agent-lab/commit/fda22904adfe1a0e4c5182bca4bc146d4832916e))

* fix: adjusts planner and financial analyst system prompt

* fix: adjusts coordinator and financial analyst system prompt


## v0.2.2 (2025-05-15)

### Bug Fixes

- Adjusts coordinator system prompt and CoordinatorRouter class
  ([#126](https://github.com/bsantanna/agent-lab/pull/126),
  [`aba396d`](https://github.com/bsantanna/agent-lab/commit/aba396dc76dacd4f5982b759b0090ffd83f86b66))


## v0.2.1 (2025-05-14)

### Bug Fixes

- Proxy timeout settings for long running operations
  ([#125](https://github.com/bsantanna/agent-lab/pull/125),
  [`fb5df21`](https://github.com/bsantanna/agent-lab/commit/fb5df2134f690de880150c2d733c2d82ac9c421c))


## v0.2.0 (2025-05-13)

### Features

- Support to tools descriptions in prompt ([#124](https://github.com/bsantanna/agent-lab/pull/124),
  [`59ab53e`](https://github.com/bsantanna/agent-lab/commit/59ab53e62ab5e662eb25f425ce744735542eee89))


## v0.1.0 (2025-05-06)

### Features

- Project library updates ([#117](https://github.com/bsantanna/agent-lab/pull/117),
  [`6701500`](https://github.com/bsantanna/agent-lab/commit/6701500c9ddf31b74c808f3dde2f445a4636b33d))

- Prototypes release workflow ([#111](https://github.com/bsantanna/agent-lab/pull/111),
  [`4837a0b`](https://github.com/bsantanna/agent-lab/commit/4837a0b90ead0f55c7300038c8a2fa8de21a49fd))
