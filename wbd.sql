--
-- PostgreSQL database dump
--

\restrict MqTUQMp6feDFNmeP0LQ917wRsCnI71V1J9y1gYFCPcHiYVCE4ns1BSdq3nXckfS

-- Dumped from database version 18.1
-- Dumped by pg_dump version 18.1

-- Started on 2025-11-16 16:56:37

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
-- TOC entry 219 (class 1259 OID 16389)
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
-- TOC entry 222 (class 1259 OID 16416)
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
-- TOC entry 220 (class 1259 OID 16395)
-- Name: ticketinfo; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ticketinfo (
    ticket_id integer NOT NULL,
    submitter_username character varying(100) NOT NULL,
    handler_helper_id integer,
    time_spent integer,
    resolution_rating smallint,
    created_at time without time zone NOT NULL,
    closed_at time without time zone NOT NULL
);


ALTER TABLE public.ticketinfo OWNER TO postgres;

--
-- TOC entry 221 (class 1259 OID 16415)
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
-- TOC entry 5014 (class 0 OID 16389)
-- Dependencies: 219
-- Data for Name: helperinfo; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.helperinfo (helper_id, admin_name, admin_rank, warnings_count) FROM stdin;
1	Valera	Moder	0
2	Richard	Admin	0
3	Nazolik	Admin	0
4	Alex Vance	Curator	0
5	Anima Zhuravlev	SuperAdmin	0
\.


--
-- TOC entry 5015 (class 0 OID 16395)
-- Dependencies: 220
-- Data for Name: ticketinfo; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.ticketinfo (ticket_id, submitter_username, handler_helper_id, time_spent, resolution_rating, created_at, closed_at) FROM stdin;
2	Alex	5	120	4	00:01:48	00:05:40
3	Fanfusic	2	75	1	13:47:26	13:50:30
4	Barny 	1	300	2	16:36:52	16:46:35
5	Domik Freeman	4	80	4	23:40:00	23:47:15
6	Gragary	5	90	3	20:52:38	20:58:30
7	Frosty	1	100	5	23:40:00	23:45:00
8	Jon	2	45	4	10:10:50	10:12:45
9	Sans Joi	3	70	2	07:37:05	07:38:15
10	Vin Kashin	3	200	3	01:53:30	01:56:50
1	Gray	5	60	5	10:00:00	10:15:00
\.


--
-- TOC entry 5023 (class 0 OID 0)
-- Dependencies: 222
-- Name: helperinfo_helper_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.helperinfo_helper_id_seq', 5, true);


--
-- TOC entry 5024 (class 0 OID 0)
-- Dependencies: 221
-- Name: ticketinfo_ticket_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.ticketinfo_ticket_id_seq', 10, true);


--
-- TOC entry 4863 (class 2606 OID 16403)
-- Name: helperinfo helperinfo_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.helperinfo
    ADD CONSTRAINT helperinfo_pkey PRIMARY KEY (helper_id);


--
-- TOC entry 4865 (class 2606 OID 16400)
-- Name: ticketinfo ticketinfo_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ticketinfo
    ADD CONSTRAINT ticketinfo_pkey PRIMARY KEY (ticket_id);


--
-- TOC entry 4866 (class 2606 OID 16409)
-- Name: ticketinfo HelperInfo.helper_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ticketinfo
    ADD CONSTRAINT "HelperInfo.helper_id" FOREIGN KEY (handler_helper_id) REFERENCES public.helperinfo(helper_id) NOT VALID;


-- Completed on 2025-11-16 16:56:37

--
-- PostgreSQL database dump complete
--

\unrestrict MqTUQMp6feDFNmeP0LQ917wRsCnI71V1J9y1gYFCPcHiYVCE4ns1BSdq3nXckfS

