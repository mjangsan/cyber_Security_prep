# crAPI Docker Troubleshooting: 502 Bad Gateway After Restart

## Overview

After an unexpected system shutdown, crAPI was started again. The Docker
Compose services appeared to be running, but the application returned
**502 Bad Gateway** when accessing a Workshop-related page.

The issue was traced to the `crapi-workshop` container exiting during
startup after it failed to connect to the Identity service. Starting the
Workshop container again after Identity was available resolved the
issue.

This note records the symptoms, investigation, resolution, and lessons
learned.

## Environment

-   Platform: Kali Linux VM
-   Deployment: OWASP crAPI using Docker Compose
-   Compose files:
    -   `deploy/docker/docker-compose.yml`
    -   `deploy/docker/docker-compose.minimal.yml`
-   Compose command used: `docker-compose`
-   Frontend URL: `http://127.0.0.1:8888`

Run Compose commands from the deployment directory:

``` bash
cd /root/Desktop/crAPI/deploy/docker
```

For this deployment, include both Compose files in commands:

``` bash
-f docker-compose.yml -f docker-compose.minimal.yml
```

## Symptoms

-   The crAPI frontend loaded.
-   Some pages or API requests returned **502 Bad Gateway**.
-   Docker showed most services as running/healthy, but that did not
    guarantee every application process was functioning.
-   The failing request observed in the browser was:

``` http
GET /workshop/api/shop/products?limit=30&offset=0
```

The frontend Nginx log showed an upstream connection failure:

``` text
connect() failed (113: Host is unreachable) while connecting to upstream
```

The upstream shown in that log was:

``` text
https://172.18.0.10:8000/workshop/api/shop/products
```

## Investigation

### 1. Check the Compose service status

``` bash
docker-compose \
  -f docker-compose.yml \
  -f docker-compose.minimal.yml \
  ps
```

A service can appear to be running, or have a passing container health
check, without proving that every application-level dependency is ready.

### 2. Inspect the frontend logs

``` bash
docker logs crapi-web --tail 50
```

The Nginx log showed that requests to the Workshop upstream were
failing.

### 3. Inspect the Workshop logs

``` bash
docker logs crapi-workshop --tail 80
```

The important error was a connection failure when Workshop tried to
contact Identity:

``` text
Failed to ping identity server:
HTTPSConnectionPool(host='crapi-identity', port=8080, ...)

Connection refused
```

The log then reported:

``` text
Django database seeding failed.
Exiting in 5 seconds.
```

### 4. Check the Workshop container state

``` bash
docker inspect crapi-workshop \
  --format 'Status={{.State.Status}} Restarting={{.State.Restarting}} ExitCode={{.State.ExitCode}}'
```

The observed result was:

``` text
Status=exited Restarting=false ExitCode=1
```

The Workshop IP-address inspection returned no address because the
stopped container did not have an active network endpoint.

Identity was running and had an IP address on the Docker network. The
Docker network inspection also showed the running service endpoints.

## Cause

The evidence indicated a **service-readiness/startup-order problem**:

1.  The containers were restarted.
2.  Workshop attempted to contact `crapi-identity` on port `8080`.
3.  Identity refused the connection at that moment.
4.  Workshop's initialization/database-seeding step failed.
5.  Workshop exited with code `1`.
6.  The frontend could not reach the Workshop upstream and returned
    `502 Bad Gateway`.

The important distinction is that Docker successfully restarted the
container process, but the Workshop application did not complete its
initialization successfully.

The evidence supports a startup/readiness race as the likely cause. It
does not establish that every restart will fail, or that startup
ordering is the only possible cause of a future failure.

## Resolution

After confirming that Identity was running, Workshop was started
separately:

``` bash
docker-compose \
  -f docker-compose.yml \
  -f docker-compose.minimal.yml \
  start crapi-workshop
```

Workshop then initialized successfully and remained running. The crAPI
application became accessible again.

Verify the result with:

``` bash
docker-compose \
  -f docker-compose.yml \
  -f docker-compose.minimal.yml \
  ps
```

Check Workshop logs if needed:

``` bash
docker logs crapi-workshop --tail 60
```

## Why `restart` did not solve it, but `start` did

These commands have different purposes:

  -----------------------------------------------------------------------
  Command                             Behaviour
  ----------------------------------- -----------------------------------
  `docker-compose restart`            Restarts existing containers. It
                                      does not wait for application
                                      dependencies to become ready.

  `docker-compose start`              Starts existing stopped containers.
                                      It does not recreate them.

  `docker-compose up -d`              Creates or recreates services when
                                      needed and starts them.
  -----------------------------------------------------------------------

In this incident, restarting the services caused Workshop to attempt
initialization while Identity was not yet accepting connections.
Workshop exited. Starting Workshop again later worked because Identity
was already available.

**`start` is not inherently more reliable than `restart`.** It worked in
this case because it was run after the dependency had become ready.

## Useful Troubleshooting Commands

Run these from `/root/Desktop/crAPI/deploy/docker`.

### Check all services

``` bash
docker-compose \
  -f docker-compose.yml \
  -f docker-compose.minimal.yml \
  ps
```

### View Workshop logs

``` bash
docker logs crapi-workshop --tail 80
```

### View Identity logs

``` bash
docker logs crapi-identity --tail 80
```

### Inspect Workshop state

``` bash
docker inspect crapi-workshop \
  --format 'Status={{.State.Status}} ExitCode={{.State.ExitCode}}'
```

### Inspect container IP addresses

``` bash
docker inspect crapi-workshop \
  --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'

docker inspect crapi-identity \
  --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'
```

### Check Docker networks

``` bash
docker network ls
docker network inspect docker_default
```

### Start Workshop after confirming Identity is ready

``` bash
docker-compose \
  -f docker-compose.yml \
  -f docker-compose.minimal.yml \
  start crapi-workshop
```

## Lessons Learned

1.  **A running container does not necessarily mean the application
    inside it is ready.** Check application logs and health checks, not
    only the container status.
2.  **Container startup order and application readiness are different.**
    A dependency container may be running before its service is ready to
    accept connections.
3.  **A 502 response can originate from a reverse proxy failing to reach
    an upstream service.** Identify the failing request and inspect the
    proxy logs.
4.  **Use logs to find the failing component.** In this incident, the
    frontend log showed the failed Workshop upstream request, while the
    Workshop log exposed the Identity connection failure.
5.  **Avoid deleting containers or volumes during initial diagnosis.**
    Inspect state, logs, networks, and dependencies first.
6.  **Record the exact commands and observed errors.** This makes the
    environment easier to recover and helps distinguish application
    failures from infrastructure failures.

## Incident Summary

  Item                               Finding
  ---------------------------------- -----------------------------------------------------
  Symptom                            502 Bad Gateway on a Workshop request
  Failing component                  `crapi-workshop`
  Dependency involved                `crapi-identity:8080`
  Workshop exit code                 `1`
  Key error                          Identity connection refused during initialization
  Likely cause                       Workshop started before Identity was ready
  Resolution                         Started Workshop again after Identity was available
  Data/container deletion required   No

## Relevance to Web API Security Testing

A reliable test environment is essential for repeatable security
experiments. Before interpreting a failed API test as a vulnerability or
a tool-detection failure, verify that the target application and its
dependencies are operational.

For future experiments, record:

-   Whether the target service was available before testing.
-   Whether dependent services were healthy and reachable.
-   The request, response status, and relevant server logs.
-   Whether the failure was reproducible after the environment was
    restored.

This helps separate application security findings from infrastructure
and availability problems.
