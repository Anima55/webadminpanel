--
-- PostgreSQL database dump
--

\restrict eQbFIS40SusfiS2Qes8wV6ssqvIfgNopqM0nNxUSPpY1RT74UN88DNctdchUypm

-- Dumped from database version 18.1
-- Dumped by pg_dump version 18.1

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

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: helperinfo; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.helperinfo (
    helper_id integer NOT NULL,
    admin_name character varying(100) NOT NULL,
    admin_rank character varying(50) NOT NULL,
    warnings_count integer DEFAULT 0
);


ALTER TABLE public.helperinfo OWNER TO postgres;

--
-- Name: helperinfo_helper_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.helperinfo ALTER COLUMN helper_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.helperinfo_helper_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: ticketinfo; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ticketinfo (
    ticket_id integer NOT NULL,
    submitter_username character varying(100) NOT NULL,
    handler_helper_id integer,
    time_spent integer,
    resolution_rating smallint
);


ALTER TABLE public.ticketinfo OWNER TO postgres;

--
-- Name: ticketinfo_ticket_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.ticketinfo ALTER COLUMN ticket_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.ticketinfo_ticket_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: webadmin; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.webadmin (
    webadmin_id integer NOT NULL,
    webadmin_name character varying(100) NOT NULL,
    webadmin_rank character varying(50) NOT NULL,
    webadmin_password character varying(255) NOT NULL
);


ALTER TABLE public.webadmin OWNER TO postgres;

--
-- Name: webadmin_webadmin_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.webadmin ALTER COLUMN webadmin_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.webadmin_webadmin_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Data for Name: helperinfo; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.helperinfo (helper_id, admin_name, admin_rank, warnings_count) FROM stdin;
5	Anima Zhuravlev	SuperAdmin	0
2	Richard	Curator	0
3	Nazolik	Manager	0
4	Alex Vance	Admin	1
13	dsfsdf	Moder	0
\.


--
-- Data for Name: ticketinfo; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.ticketinfo (ticket_id, submitter_username, handler_helper_id, time_spent, resolution_rating) FROM stdin;
2	Alex	5	120	4
3	Fanfusic	2	75	1
5	Domik Freeman	4	80	4
6	Gragary	5	90	3
8	Jon	2	45	4
9	Sans Joi	3	70	2
10	Vin Kashin	3	200	3
1	Gray	5	60	5
\.


--
-- Data for Name: webadmin; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.webadmin (webadmin_id, webadmin_name, webadmin_rank, webadmin_password) FROM stdin;
2	Anima Zhuravlev	SuperAdmin	scrypt:32768:8:1$yzvgpIw9SqB5MoFl$bcc0e25e83328863ad368bb3431c0967f5b30a0699c98564030c0e99bee894fcc33608356839e5894b35f0f96f8e06aca34aa85a8d7586530e0f5751c9ab56d9
\.


--
-- Name: helperinfo_helper_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.helperinfo_helper_id_seq', 13, true);


--
-- Name: ticketinfo_ticket_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.ticketinfo_ticket_id_seq', 10, true);


--
-- Name: webadmin_webadmin_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.webadmin_webadmin_id_seq', 3, true);


--
-- Name: helperinfo helperinfo_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.helperinfo
    ADD CONSTRAINT helperinfo_pkey PRIMARY KEY (helper_id);


--
-- Name: ticketinfo ticketinfo_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ticketinfo
    ADD CONSTRAINT ticketinfo_pkey PRIMARY KEY (ticket_id);


--
-- Name: webadmin webadmin_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.webadmin
    ADD CONSTRAINT webadmin_pkey PRIMARY KEY (webadmin_id);


--
-- Name: ticketinfo HelperInfo.helper_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ticketinfo
    ADD CONSTRAINT "HelperInfo.helper_id" FOREIGN KEY (handler_helper_id) REFERENCES public.helperinfo(helper_id) NOT VALID;


--
-- PostgreSQL database dump complete
--

\unrestrict eQbFIS40SusfiS2Qes8wV6ssqvIfgNopqM0nNxUSPpY1RT74UN88DNctdchUypm

