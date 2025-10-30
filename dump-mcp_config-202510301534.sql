--
-- PostgreSQL database dump
--

-- Dumped from database version 17.5
-- Dumped by pg_dump version 17.5

-- Started on 2025-10-30 15:34:50

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 4 (class 2615 OID 2200)
-- Name: public; Type: SCHEMA; Schema: -; Owner: pg_database_owner
--

CREATE SCHEMA public;


ALTER SCHEMA public OWNER TO pg_database_owner;

--
-- TOC entry 4883 (class 0 OID 0)
-- Dependencies: 4
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: pg_database_owner
--

COMMENT ON SCHEMA public IS 'standard public schema';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 220 (class 1259 OID 58886)
-- Name: agent_mcp_servers; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.agent_mcp_servers (
    agent_id uuid NOT NULL,
    server_id character varying(255) NOT NULL
);


ALTER TABLE public.agent_mcp_servers OWNER TO postgres;

--
-- TOC entry 219 (class 1259 OID 58876)
-- Name: agents; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.agents (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.agents OWNER TO postgres;

--
-- TOC entry 217 (class 1259 OID 58843)
-- Name: mcp_servers; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.mcp_servers (
    id character varying NOT NULL,
    name character varying,
    url character varying,
    status character varying,
    enabled boolean,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.mcp_servers OWNER TO postgres;

--
-- TOC entry 218 (class 1259 OID 58854)
-- Name: tools; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tools (
    id character varying NOT NULL,
    name character varying,
    description text,
    parameters json,
    server_id character varying,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    api_url text,
    http_method text DEFAULT 'GET'::text,
    request_headers json,
    request_body json
);


ALTER TABLE public.tools OWNER TO postgres;

--
-- TOC entry 4877 (class 0 OID 58886)
-- Dependencies: 220
-- Data for Name: agent_mcp_servers; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.agent_mcp_servers (agent_id, server_id) FROM stdin;
e62f535c-3a82-4e79-bf87-a908640bf543	f2f47d1f-3fcd-4cee-b560-2a89f510a6f2
61acc92a-fea9-4b31-a5de-fe26c123f959	finance-server-001
5717ae7e-bbf3-4246-a4e0-2cb9f48c74b3	finance-server-001
5717ae7e-bbf3-4246-a4e0-2cb9f48c74b3	f2f47d1f-3fcd-4cee-b560-2a89f510a6f2
5717ae7e-bbf3-4246-a4e0-2cb9f48c74b3	a064f709-621c-4d24-9337-223994c853bc
\.


--
-- TOC entry 4876 (class 0 OID 58876)
-- Dependencies: 219
-- Data for Name: agents; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.agents (id, name, description, created_at, updated_at) FROM stdin;
e62f535c-3a82-4e79-bf87-a908640bf543	Weather	Weather Tools	2025-10-16 11:32:52.05532+07	2025-10-16 11:32:52.05532+07
61acc92a-fea9-4b31-a5de-fe26c123f959	Stock	Stock Tools	2025-10-16 13:06:57.556015+07	2025-10-16 13:06:57.556015+07
5717ae7e-bbf3-4246-a4e0-2cb9f48c74b3	2 in 1	2 in 1 Tools	2025-10-16 13:59:16.635329+07	2025-10-16 13:59:16.635329+07
\.


--
-- TOC entry 4874 (class 0 OID 58843)
-- Dependencies: 217
-- Data for Name: mcp_servers; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.mcp_servers (id, name, url, status, enabled, created_at, updated_at) FROM stdin;
a064f709-621c-4d24-9337-223994c853bc	Unnamed Server	http://192.168.1.6:3001	connected	t	2025-10-16 15:47:21.037854+07	2025-10-16 15:47:21.037854+07
finance-server-001	MCP Server 1	http://localhost:3001	connected	t	2025-10-08 13:26:18.427252+07	2025-10-08 14:56:16.028521+07
f2f47d1f-3fcd-4cee-b560-2a89f510a6f2	MCP Server 2	http://localhost:3002	connected	t	2025-10-15 14:27:57.897099+07	2025-10-15 14:27:57.897099+07
\.


--
-- TOC entry 4875 (class 0 OID 58854)
-- Dependencies: 218
-- Data for Name: tools; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.tools (id, name, description, parameters, server_id, created_at, updated_at, api_url, http_method, request_headers, request_body) FROM stdin;
finance-tool-001	get_stock_price	Get current stock price for a specific symbol	[{"name": "symbol", "type": "string", "description": "Stock symbol", "required": true}]	finance-server-001	2025-10-08 13:26:18.427252+07	2025-10-08 13:26:18.427252+07	\N	GET	\N	\N
finance-tool-002	calculate_portfolio	Calculate portfolio value and performance	[{"name": "stocks", "type": "object", "description": "Stock holdings", "required": true}]	finance-server-001	2025-10-08 13:26:18.427252+07	2025-10-08 13:26:18.427252+07	\N	GET	\N	\N
finance-tool-003	get_financial_news	Get latest financial news	[{"name": "topic", "type": "string", "description": "Topic or company", "required": true}, {"name": "limit", "type": "integer", "description": "Number of articles", "required": false}]	finance-server-001	2025-10-08 13:26:18.427252+07	2025-10-08 13:26:18.427252+07	\N	GET	\N	\N
11b11b87-676a-4c3b-81fa-a04550f9425b	get_weather	Get current weather for a specific city	[{"name": "location", "type": "string", "description": "Location parameter", "required": true}]	f2f47d1f-3fcd-4cee-b560-2a89f510a6f2	2025-10-15 15:37:39.413073+07	2025-10-15 15:37:39.413073+07	\N	GET	\N	\N
00dc9678-e3a8-404f-8112-fec36777d5b5	get_time	Get current time for a specific timezone	[{"name": "location", "type": "string", "description": "Location parameter", "required": true}]	f2f47d1f-3fcd-4cee-b560-2a89f510a6f2	2025-10-15 15:37:48.204215+07	2025-10-15 15:37:48.204215+07	\N	GET	\N	\N
c48e3767-9977-4f80-985f-600361ca1516	get_info_servers	All MCP Server Information 	[{"description": "MCP Keyword", "name": "question", "required": true, "type": "string"}]	finance-server-001	2025-10-16 13:40:21.130251+07	2025-10-16 13:40:21.130251+07	http://localhost:3000/servers	GET	\N	\N
\.


--
-- TOC entry 4725 (class 2606 OID 58890)
-- Name: agent_mcp_servers agent_mcp_servers_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.agent_mcp_servers
    ADD CONSTRAINT agent_mcp_servers_pkey PRIMARY KEY (agent_id, server_id);


--
-- TOC entry 4723 (class 2606 OID 58885)
-- Name: agents agents_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.agents
    ADD CONSTRAINT agents_pkey PRIMARY KEY (id);


--
-- TOC entry 4717 (class 2606 OID 58851)
-- Name: mcp_servers mcp_servers_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mcp_servers
    ADD CONSTRAINT mcp_servers_pkey PRIMARY KEY (id);


--
-- TOC entry 4721 (class 2606 OID 58862)
-- Name: tools tools_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tools
    ADD CONSTRAINT tools_pkey PRIMARY KEY (id);


--
-- TOC entry 4714 (class 1259 OID 58852)
-- Name: ix_mcp_servers_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_mcp_servers_id ON public.mcp_servers USING btree (id);


--
-- TOC entry 4715 (class 1259 OID 58853)
-- Name: ix_mcp_servers_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_mcp_servers_name ON public.mcp_servers USING btree (name);


--
-- TOC entry 4718 (class 1259 OID 58869)
-- Name: ix_tools_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_tools_id ON public.tools USING btree (id);


--
-- TOC entry 4719 (class 1259 OID 58868)
-- Name: ix_tools_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_tools_name ON public.tools USING btree (name);


--
-- TOC entry 4727 (class 2606 OID 58891)
-- Name: agent_mcp_servers agent_mcp_servers_agent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.agent_mcp_servers
    ADD CONSTRAINT agent_mcp_servers_agent_id_fkey FOREIGN KEY (agent_id) REFERENCES public.agents(id) ON DELETE CASCADE;


--
-- TOC entry 4728 (class 2606 OID 58896)
-- Name: agent_mcp_servers agent_mcp_servers_server_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.agent_mcp_servers
    ADD CONSTRAINT agent_mcp_servers_server_id_fkey FOREIGN KEY (server_id) REFERENCES public.mcp_servers(id) ON DELETE CASCADE;


--
-- TOC entry 4726 (class 2606 OID 58863)
-- Name: tools tools_server_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tools
    ADD CONSTRAINT tools_server_id_fkey FOREIGN KEY (server_id) REFERENCES public.mcp_servers(id);


-- Completed on 2025-10-30 15:34:50

--
-- PostgreSQL database dump complete
--

