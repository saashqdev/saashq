import { Calendar as FullCalendar } from "@fullcalendar/core";
import dayGridPlugin from "@fullcalendar/daygrid";
import listPlugin from "@fullcalendar/list";
import timeGridPlugin from "@fullcalendar/timegrid";
import interactionPlugin from "@fullcalendar/interaction";

saashq.FullCalendar = FullCalendar;
saashq.FullCalendar.Plugins = [listPlugin, dayGridPlugin, timeGridPlugin, interactionPlugin];
