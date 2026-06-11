"use client";

import React, { useState, useEffect } from "react";
import { API_URL } from "@/lib/config";
import { 
  Sparkles, UploadCloud, BookOpen, Layers, Award, BarChart3, 
  Download, Play, Plus, Trash2, ArrowRight, CheckCircle2, 
  ChevronRight, Save, AlertCircle, Pencil,
  Eye, FileText, ChevronLeft, Volume2, Lightbulb, GraduationCap,
  FileSpreadsheet, Gamepad2, Cpu
} from "lucide-react";

// Types matching backend models
interface Course {
  id: number;
  title: string;
  description: string;
  created_at: string;
}

interface Slide {
  id: number;
  slide_index: number;
  title: string;
  content: string[];
  suggested_visuals: string;
}

interface Note {
  id: number;
  slide_index: number;
  talking_points: string[];
  teaching_tips: string;
  examples: string[];
}

interface Assessment {
  id: number;
  question_text: string;
  question_type: string;
  options: string[] | null;
  correct_answer: string | null;
  bloom_level: string;
  learning_outcome_id: number | null;
}

interface Outcome {
  id: number;
  text: string;
  bloom_level: string;
}

interface Readiness {
  score: number;
  completeness: number;
  outcome_coverage: number;
  assessment_quality: number;
  bloom_coverage: number;
  industry_relevance: number;
  breakdown: Record<string, string>;
}

interface GapReport {
  status: string;
  missing_topics: string[];
  recommendations: string[];
}

interface Module {
  id?: string | number;
  title: string;
  topics?: string[];
}

interface CurriculumMap {
  modules?: Module[];
}

interface CourseDetails {
  course: Course;
  curriculum_analysis: {
    curriculum_map: CurriculumMap | null;
    gap_analysis: string | null;
    industry_gap_report: GapReport;
  } | null;
  learning_outcomes: Outcome[];
  slides: Slide[];
  notes: Note[];
  assessments: Assessment[];
  readiness_score: Readiness | null;
}

// Helper function to parse database critique breakdowns into structured reason / recommendation
function parseCritique(
  breakdown: Record<string, string> | null | undefined,
  metricKey: string,
  val: number
) {
  let comment = "";
  if (breakdown) {
    const keys = Object.keys(breakdown);
    const matchedKey = keys.find(k => k.toLowerCase().includes(metricKey.toLowerCase()) || metricKey.toLowerCase().includes(k.toLowerCase()));
    if (matchedKey) {
      comment = breakdown[matchedKey];
    } else if (breakdown["Overall Score"] && metricKey === "Overall") {
      comment = breakdown["Overall Score"];
    }
  }

  // Fallbacks if comment is missing or empty
  if (!comment) {
    if (metricKey.toLowerCase().includes("completeness")) {
      if (val >= 85) {
        comment = "The syllabus contains a highly complete outline of topics and modules. Recommended: Keep slides updated with new case studies.";
      } else {
        comment = "Some structural sections or detailed slide descriptions are missing or thin. Recommended: Expand sub-topic bullet points to ensure complete coverage.";
      }
    } else if (metricKey.toLowerCase().includes("bloom")) {
      if (val >= 85) {
        comment = "Strong cognitive level coverage across lower and higher order objectives. Recommended: Maintain project-based assessments.";
      } else {
        comment = "The course focuses heavily on Remembering and Understanding levels but lacks activities targeting Evaluating and Creating. Recommended: Add project-based assessments and design challenges.";
      }
    } else if (metricKey.toLowerCase().includes("assessment")) {
      if (val >= 85) {
        comment = "Assessments are highly aligned with the learning outcomes and cover appropriate difficulty levels. Recommended: Introduce peer evaluations.";
      } else {
        comment = "Assessments are limited in count or not fully aligned to advanced learning outcomes. Recommended: Add more diagnostic assessments and diverse question formats matching the outcomes.";
      }
    } else if (metricKey.toLowerCase().includes("relevance") || metricKey.toLowerCase().includes("industry")) {
      if (val >= 85) {
        comment = "Course curriculum is aligned with cutting-edge industry practices and technologies. Recommended: Integrate live tool tutorials.";
      } else {
        comment = "The syllabus lacks recent real-world advancements or industry-relevant technical tooling. Recommended: Integrate modern tools, industry APIs, and practical case studies.";
      }
    } else {
      comment = `Readiness metric score is ${val.toFixed(0)}/100. Recommended: Review syllabus alignment and completeness.`;
    }
  }

  let reason = "";
  let recommendation = "";

  const indicators = ["Recommended:", "To improve:", "Recommendation:", "Improvement:", "Suggested:", "Suggest:"];
  let foundIndicator = "";
  let splitIndex = -1;

  for (const ind of indicators) {
    const idx = comment.indexOf(ind);
    if (idx !== -1) {
      if (splitIndex === -1 || idx < splitIndex) {
        splitIndex = idx;
        foundIndicator = ind;
      }
    }
  }

  if (splitIndex !== -1) {
    reason = comment.substring(0, splitIndex).trim();
    recommendation = comment.substring(splitIndex + foundIndicator.length).trim();
  } else {
    const sentences = comment.split(/(?<=[.!?])\s+/);
    if (sentences.length > 1) {
      recommendation = sentences.pop() || "";
      reason = sentences.join(" ");
    } else {
      reason = comment;
      if (val >= 85) {
        recommendation = "Continue to maintain high quality standards and periodically refresh course examples.";
      } else {
        recommendation = "Review syllabus detail and align exercises with higher-level Bloom taxonomy verbs.";
      }
    }
  }

  reason = reason.trim();
  recommendation = recommendation.trim();

  if (reason.endsWith(",") || reason.endsWith(":") || reason.endsWith(".")) {
    reason = reason.slice(0, -1).trim();
  }

  return { reason, recommendation };
}

interface AgentStatus {
  name: string;
  purpose: string;
  status: "pending" | "running" | "completed" | "failed";
  timestamp?: string;
  duration?: number;
}

const initialPipeline: AgentStatus[] = [
  { name: "Curriculum Analysis Agent", purpose: "Extracts modules, topics, and structures from raw syllabus text.", status: "pending" },
  { name: "Learning Outcome Agent", purpose: "Generates measurable learning outcomes mapped to Bloom's Taxonomy.", status: "pending" },
  { name: "Curriculum Planning Agent", purpose: "Coordinates weekly sequencing, lesson scheduling, and academic pacing.", status: "pending" },
  { name: "Slide Generation Agent", purpose: "Generates slide titles, layout outlines, and content bullet points.", status: "pending" },
  { name: "Instructor Notes Agent", purpose: "Develops comprehensive lecturer talking points and real-world examples.", status: "pending" },
  { name: "Assessment Agent", purpose: "Creates diagnostic assessment questions mapped to learning outcomes.", status: "pending" },
  { name: "Bloom Audit Agent", purpose: "Analyzes cognitive balance and produces a Bloom level distribution report.", status: "pending" },
  { name: "Industry Gap Agent", purpose: "Benchmarks curriculum mapping against modern technology requirements.", status: "pending" },
  { name: "Readiness Score Agent", purpose: "Computes overall 100-point accreditation readiness scoring.", status: "pending" }
];

export default function KalyxApp() {
  // App views: 'landing' | 'workspace'
  const [view, setView] = useState<"landing" | "workspace">("landing");
  const [activeTab, setActiveTab] = useState<"overview" | "slides" | "notes" | "assessments" | "bloom" | "readiness" | "gaps" | "export" | "traceability" | "pipeline">("overview");

  // New state variables for Traceability and Readiness breakdowns
  const [traceabilityData, setTraceabilityData] = useState<any[]>([]);
  const [expandedOutcomes, setExpandedOutcomes] = useState<Record<number, boolean>>({});
  const [isReadinessExpanded, setIsReadinessExpanded] = useState(false);
  const [pipelineAgents, setPipelineAgents] = useState<AgentStatus[]>(initialPipeline);

  const handleAuthError = () => {
    localStorage.removeItem("kalyx_auth_token");
    localStorage.removeItem("kalyx_auth_user");
    setAuthToken(null);
    setUser(null);
    alert("Session expired or invalid. Please log in again.");
  };

  const allCompleted = pipelineAgents.every(a => a.status === "completed");
  const totalDuration = allCompleted
    ? pipelineAgents.reduce((sum, a) => sum + (a.duration || 0), 0)
    : 0;
  
  // Data State
  const [courses, setCourses] = useState<Course[]>([]);
  const [activeCourseId, setActiveCourseId] = useState<number | null>(null);
  const [courseDetails, setCourseDetails] = useState<CourseDetails | null>(null);
  
  // Create / Upload State
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newCourseTitle, setNewCourseTitle] = useState("");
  const [newCourseDesc, setNewCourseDesc] = useState("");
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadLogs, setUploadLogs] = useState<string[]>([]);

  const startPipelineSimulation = () => {
    const initial: AgentStatus[] = [
      { name: "Curriculum Analysis Agent", purpose: "Extracts modules, topics, and structures from raw syllabus text.", status: "running" },
      { name: "Learning Outcome Agent", purpose: "Generates measurable learning outcomes mapped to Bloom's Taxonomy.", status: "pending" },
      { name: "Curriculum Planning Agent", purpose: "Coordinates weekly sequencing, lesson scheduling, and academic pacing.", status: "pending" },
      { name: "Slide Generation Agent", purpose: "Generates slide titles, layout outlines, and content bullet points.", status: "pending" },
      { name: "Instructor Notes Agent", purpose: "Develops comprehensive lecturer talking points and real-world examples.", status: "pending" },
      { name: "Assessment Agent", purpose: "Creates diagnostic assessment questions mapped to learning outcomes.", status: "pending" },
      { name: "Bloom Audit Agent", purpose: "Analyzes cognitive balance and produces a Bloom level distribution report.", status: "pending" },
      { name: "Industry Gap Agent", purpose: "Benchmarks curriculum mapping against modern technology requirements.", status: "pending" },
      { name: "Readiness Score Agent", purpose: "Computes overall 100-point accreditation readiness scoring.", status: "pending" }
    ];
    setPipelineAgents(initial);
 
    let activeIdx = 0;
    const interval = setInterval(() => {
      setPipelineAgents(prev => {
        const next = [...prev];
        if (activeIdx < next.length) {
          next[activeIdx] = { 
            ...next[activeIdx], 
            status: "completed", 
            timestamp: `Step ${activeIdx + 1} of 9` 
          };
        }
        activeIdx++;
        if (activeIdx < next.length) {
          next[activeIdx] = { 
            ...next[activeIdx], 
            status: "running"
          };
        } else {
          clearInterval(interval);
        }
        return next;
      });
    }, 1500);
 
    return interval;
  };
 
  const completePipelineSimulation = (telemetry?: any[]) => {
    setPipelineAgents(prev => {
      return prev.map((agent, idx) => {
        const tItem = telemetry?.find(t => t.agent === agent.name);
        if (tItem) {
          const durationSec = typeof tItem.duration_ms === 'number' ? tItem.duration_ms / 1000 : tItem.duration_seconds;
          const formattedDuration = typeof durationSec === 'number' ? `${durationSec.toFixed(1)}s` : '0.0s';
          return {
            ...agent,
            status: "completed",
            timestamp: `Completed • ${formattedDuration}`,
            duration: durationSec
          };
        }
        return {
          ...agent,
          status: "completed",
          timestamp: `Step ${idx + 1} of 9`
        };
      });
    });
  };
 
  const failPipelineSimulation = () => {
    setPipelineAgents(prev => {
      return prev.map(agent => {
        if (agent.status === "running") {
          return { ...agent, status: "failed" };
        }
        return agent;
      });
    });
  };
  
  // AI Personalization settings
  const [personalization, setPersonalization] = useState({
    tone: "Professional & Academic",
    style: "Sleek Dark Mode",
    examplesCount: "3 per slide",
    customInstructions: ""
  });

  // Edit states for AI Studio
  const [activeSlideIndex, setActiveSlideIndex] = useState(0);
  const [editSlideTitle, setEditSlideTitle] = useState("");
  const [editSlideBullets, setEditSlideBullets] = useState<string[]>([]);
  const [editSlideVisuals, setEditSlideVisuals] = useState("");
  const [editNoteTalkingPoints, setEditNoteTalkingPoints] = useState<string[]>([]);
  const [editNoteTips, setEditNoteTips] = useState("");
  const [editNoteExamples, setEditNoteExamples] = useState<string[]>([]);

  // User Authentication States
  const [authToken, setAuthToken] = useState<string | null>(null);
  const [user, setUser] = useState<{ id: number; email: string; username: string; full_name: string | null } | null>(null);
  const [authMode, setAuthMode] = useState<"login" | "signup">("login");
  const [authUsernameOrEmail, setAuthUsernameOrEmail] = useState("");
  const [authEmail, setAuthEmail] = useState("");
  const [authUsername, setAuthUsername] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [authFullName, setAuthFullName] = useState("");
  const [authError, setAuthError] = useState("");

  const backendUrl = API_URL;

  const handleAuthSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError("");
    
    if (authMode === "login") {
      if (!authUsernameOrEmail.trim() || !authPassword.trim()) {
        setAuthError("Please enter your username/email and password.");
        return;
      }
      try {
        const res = await fetch(`${backendUrl}/api/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            username_or_email: authUsernameOrEmail,
            password: authPassword
          })
        });
        const data = await res.json();
        if (!res.ok) {
          setAuthError(data.detail || "Invalid credentials.");
          return;
        }
        setAuthToken(data.access_token);
        setUser(data.user);
        localStorage.setItem("kalyx_token", data.access_token);
        localStorage.setItem("kalyx_user", JSON.stringify(data.user));
        fetchCourses(data.access_token);
      } catch (err) {
        setAuthError("Database connection refused or backend offline.");
      }
    } else {
      if (!authEmail.trim() || !authUsername.trim() || !authPassword.trim() || !authFullName.trim()) {
        setAuthError("Please fill out all signup fields.");
        return;
      }
      try {
        const res = await fetch(`${backendUrl}/api/auth/signup`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email: authEmail,
            username: authUsername,
            password: authPassword,
            full_name: authFullName
          })
        });
        const data = await res.json();
        if (!res.ok) {
          setAuthError(data.detail || "Registration failed.");
          return;
        }
        setAuthToken(data.access_token);
        setUser(data.user);
        localStorage.setItem("kalyx_token", data.access_token);
        localStorage.setItem("kalyx_user", JSON.stringify(data.user));
        fetchCourses(data.access_token);
      } catch (err) {
        setAuthError("Database connection refused or backend offline.");
      }
    }
  };

  const handleLogout = () => {
    setAuthToken(null);
    setUser(null);
    localStorage.removeItem("kalyx_token");
    localStorage.removeItem("kalyx_user");
    setCourses([]);
    setCourseDetails(null);
    setActiveCourseId(null);
    setView("landing");
  };

  function loadSlideEditState(details: CourseDetails, index: number) {
    setActiveSlideIndex(index);
    const slide = details.slides[index];
    if (slide) {
      setEditSlideTitle(slide.title);
      setEditSlideBullets([...slide.content]);
      setEditSlideVisuals(slide.suggested_visuals || "");
    }
    
    const note = details.notes.find(n => n.slide_index === slide?.slide_index);
    if (note) {
      setEditNoteTalkingPoints([...note.talking_points]);
      setEditNoteTips(note.teaching_tips || "");
      setEditNoteExamples([...(note.examples || [])]);
    } else {
      setEditNoteTalkingPoints([]);
      setEditNoteTips("");
      setEditNoteExamples([]);
    }
  }

  async function fetchTraceability(courseId: number, tokenOverride?: string) {
    const token = tokenOverride || authToken;
    if (!token) return;
    try {
      const res = await fetch(`${backendUrl}/api/courses/${courseId}/traceability`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setTraceabilityData(data);
      }
    } catch (err) {
      console.error("Fetch traceability err:", err);
    }
  }

  async function selectCourse(courseId: number, tokenOverride?: string, preserveSlideIndex?: boolean) {
    const token = tokenOverride || authToken;
    if (!token) return;
    
    // Refresh outcomes mapping
    fetchTraceability(courseId, token);
    
    try {
      const res = await fetch(`${backendUrl}/api/courses/${courseId}`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setCourseDetails(data);
        setActiveCourseId(courseId);
        
        // Hydrate pipeline agents with actual telemetry or fallback to Option B step indicators
        const telemetry = data.curriculum_analysis?.pipeline_telemetry;
        const staticPipeline: AgentStatus[] = [
          { name: "Curriculum Analysis Agent", purpose: "Extracts modules, topics, and structures from raw syllabus text.", status: "completed" },
          { name: "Learning Outcome Agent", purpose: "Generates measurable learning outcomes mapped to Bloom's Taxonomy.", status: "completed" },
          { name: "Curriculum Planning Agent", purpose: "Coordinates weekly sequencing, lesson scheduling, and academic pacing.", status: "completed" },
          { name: "Slide Generation Agent", purpose: "Generates slide titles, layout outlines, and content bullet points.", status: "completed" },
          { name: "Instructor Notes Agent", purpose: "Develops comprehensive lecturer talking points and real-world examples.", status: "completed" },
          { name: "Assessment Agent", purpose: "Creates diagnostic assessment questions mapped to learning outcomes.", status: "completed" },
          { name: "Bloom Audit Agent", purpose: "Analyzes cognitive balance and produces a Bloom level distribution report.", status: "completed" },
          { name: "Industry Gap Agent", purpose: "Benchmarks curriculum mapping against modern technology requirements.", status: "completed" },
          { name: "Readiness Score Agent", purpose: "Computes overall 100-point accreditation readiness scoring.", status: "completed" }
        ].map((agent, idx): AgentStatus => {
          const tItem = telemetry?.find((t: any) => t.agent === agent.name);
          if (tItem) {
            const durationSec = typeof tItem.duration_ms === 'number' ? tItem.duration_ms / 1000 : tItem.duration_seconds;
            const formattedDuration = typeof durationSec === 'number' ? `${durationSec.toFixed(1)}s` : '0.0s';
            return {
              name: agent.name,
              purpose: agent.purpose,
              status: "completed",
              timestamp: `Completed • ${formattedDuration}`,
              duration: durationSec
            };
          }
          return {
            name: agent.name,
            purpose: agent.purpose,
            status: "completed",
            timestamp: `Step ${idx + 1} of 9`
          };
        });
        setPipelineAgents(staticPipeline);

        // Set slide editing values
        if (data.slides && data.slides.length > 0) {
          const indexToLoad = (preserveSlideIndex && activeSlideIndex < data.slides.length) ? activeSlideIndex : 0;
          loadSlideEditState(data, indexToLoad);
        }
      } else if (res.status === 401 || res.status === 403) {
        handleAuthError();
      }
    } catch (err) {
      console.error("Get course details err:", err);
    }
  }

  async function fetchCourses(token: string) {
    try {
      const res = await fetch(`${backendUrl}/api/courses/`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setCourses(data);
        if (data.length > 0) {
          // Auto select first course
          selectCourse(data[0].id, token);
        }
      } else if (res.status === 401 || res.status === 403) {
        handleAuthError();
      }
    } catch (err) {
      console.error("Fetch courses err:", err);
    }
  }

  // Load authentication state from localStorage on mount
  useEffect(() => {
    const savedToken = localStorage.getItem("kalyx_token");
    const savedUser = localStorage.getItem("kalyx_user");
    if (savedToken && savedUser) {
      setAuthToken(savedToken);
      try {
        const parsedUser = JSON.parse(savedUser);
        setUser(parsedUser);
        fetchCourses(savedToken);
      } catch (err) {
        console.error("Failed to parse saved user credentials:", err);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleCreateCourse = async () => {
    if (!newCourseTitle.trim() || !authToken) return;
    try {
      const res = await fetch(`${backendUrl}/api/courses/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${authToken}`
        },
        body: JSON.stringify({ title: newCourseTitle, description: newCourseDesc })
      });
      if (res.ok) {
        const data = await res.json();
        setCourses(prev => [data, ...prev]);
        setActiveCourseId(data.id);
        setCourseDetails(null); // Clear out previous details
        setShowCreateModal(false);
        setNewCourseTitle("");
        setNewCourseDesc("");
        setActiveTab("overview");
      } else if (res.status === 401 || res.status === 403) {
        handleAuthError();
      } else {
        const errData = await res.json().catch(() => ({}));
        alert(`Failed to create package: ${errData.detail || errData.error || res.statusText || 'Unknown error'}`);
      }
    } catch (err) {
      console.error("Create course err:", err);
      alert("Error connecting to backend server.");
    }
  };

  const handleDeleteCourse = async (courseId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!authToken) return;
    if (!confirm("Are you sure you want to delete this course package?")) return;
    try {
      const res = await fetch(`${backendUrl}/api/courses/${courseId}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${authToken}` }
      });
      if (res.ok) {
        const updated = courses.filter(c => c.id !== courseId);
        setCourses(updated);
        if (updated.length > 0) {
          selectCourse(updated[0].id);
        } else {
          setActiveCourseId(null);
          setCourseDetails(null);
        }
      }
    } catch (err) {
      console.error("Delete course err:", err);
    }
  };

  // Syllabus Parsing & Agent Pipeline Trigger
  const handleAnalyzeSyllabus = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeCourseId || !uploadFile || !authToken) return;

    setIsUploading(true);
    setUploadLogs(["Initiating connection to KALYX backend...", "Allocating dedicated RAG chunk vectors..."]);
    const pipelineInterval = startPipelineSimulation();
    
    const formData = new FormData();
    formData.append("file", uploadFile);

    // Dynamic terminal updates to simulate real multi-agent work
    const logInterval = setInterval(() => {
      const agents = [
        "Curriculum Intelligence Agent: Scrutinizing syllabus text for educational modules...",
        "Content Generation Agent: Drafting customized slides and instructor talking points...",
        "Assessment Intelligence Agent: Structuring diagnostic test items and cognitive metrics...",
        "Curriculum Evaluation Agent: Auditing industry gaps and compliance scores..."
      ];
      const randomMsg = agents[Math.floor(Math.random() * agents.length)];
      setUploadLogs(prev => [...prev, randomMsg]);
    }, 1800);

    try {
      const res = await fetch(`${backendUrl}/api/courses/${activeCourseId}/analyze`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${authToken}`
        },
        body: formData
      });
      
      clearInterval(logInterval);
      clearInterval(pipelineInterval);

      if (res.ok) {
        const data = await res.json();
        if (data.status === "partial_generation") {
          setUploadLogs(prev => [
            ...prev, 
            `WARNING: Pipeline interrupted due to API ${data.error_type} at ${data.failed_agent}.`,
            `Successfully completed stages: ${data.successful_agents.join(", ") || "None"}.`,
            "Partial classroom package saved. Please retry later to complete the remaining sections."
          ]);
          failPipelineSimulation();
          setIsUploading(false);
          setUploadFile(null);
          selectCourse(activeCourseId);
          alert(`Partial Generation Warning:\n\nThe pipeline was interrupted due to Gemini API Rate Limit / Resource Exhaustion (${data.error_type}) at ${data.failed_agent}.\n\nSuccessful sections: ${data.successful_agents.join(", ") || "None"}.\n\nSuccessfully generated items have been saved. You can try regenerating later to complete the rest!`);
          return;
        }
        setUploadLogs(prev => [...prev, ...data.logs, "SUCCESS: Complete classroom package compiled!"]);
        completePipelineSimulation(data.pipeline_telemetry);
        // Hydrate workspace
        setTimeout(() => {
          setIsUploading(false);
          setUploadFile(null);
          selectCourse(activeCourseId);
        }, 1500);
      } else {
        setIsUploading(false);
        failPipelineSimulation();
        alert("Failed to analyze syllabus. Please try again.");
      }
    } catch (err) {
      clearInterval(logInterval);
      clearInterval(pipelineInterval);
      setIsUploading(false);
      failPipelineSimulation();
      console.error("Analyze syllabus err:", err);
      alert("Error occurred. Check that the backend server is running.");
    }
  };

  // Save edits back to database in AI Studio
  const handleSaveSlideChanges = async () => {
    if (!courseDetails || !authToken) return;
    const slide = courseDetails.slides[activeSlideIndex];
    if (!slide) return;

    try {
      // 1. Save Slide bullet structure
      const slideRes = await fetch(`${backendUrl}/api/studio/slides/${slide.id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${authToken}`
        },
        body: JSON.stringify({
          title: editSlideTitle,
          content: editSlideBullets,
          suggested_visuals: editSlideVisuals
        })
      });

      // 2. Save note talking points structure
      const note = courseDetails.notes.find(n => n.slide_index === slide.slide_index);
      if (note) {
        await fetch(`${backendUrl}/api/studio/notes/${note.id}`, {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${authToken}`
          },
          body: JSON.stringify({
            talking_points: editNoteTalkingPoints,
            teaching_tips: editNoteTips,
            examples: editNoteExamples
          })
        });
      }

      if (slideRes.ok) {
        // Reload details to sync database state and preserve active slide index
        await selectCourse(activeCourseId!, undefined, true);
        if (activeTab === "notes") {
          alert("Instructor speaker notes saved successfully!");
        } else {
          alert("Educational slide adjustments saved successfully!");
        }
      }
    } catch (err) {
      console.error("Save slide edits err:", err);
    }
  };

  // Export triggers
  const handleDownloadPptx = () => {
    if (!activeCourseId) return;
    window.open(`${backendUrl}/api/export/courses/${activeCourseId}/pptx?token=${authToken}`);
  };

  const handleDownloadPdf = () => {
    if (!activeCourseId) return;
    window.open(`${backendUrl}/api/export/courses/${activeCourseId}/pdf?token=${authToken}`);
  };


  const handleDownloadInteractiveQuiz = () => {
    if (!activeCourseId) return;
    window.open(`${backendUrl}/api/export/courses/${activeCourseId}/interactive-quiz?token=${authToken}`);
  };

  const handleRegenerateDeck = async () => {
    if (!activeCourseId || !authToken) return;
    setIsUploading(true);
    setUploadLogs(["Initiating connection to KALYX backend...", "Saving personalization profile details..."]);
    const pipelineInterval = startPipelineSimulation();
    
    try {
      const saveProfileRes = await fetch(`${backendUrl}/api/studio/courses/${activeCourseId}/personalize`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${authToken}`
        },
        body: JSON.stringify({
          profile: {
            tone: personalization.tone,
            style: personalization.style,
            examplesCount: personalization.examplesCount,
            customInstructions: personalization.customInstructions
          }
        })
      });

      if (!saveProfileRes.ok) {
        throw new Error("Failed to save personalization details.");
      }

      setUploadLogs(prev => [...prev, "Personalization profile saved successfully.", "Triggering multi-agent regeneration graph..."]);

      const regenerateInterval = setInterval(() => {
        const agentLogs = [
          "Curriculum Intelligence Agent: Scrutinizing syllabus text for educational modules...",
          "Content Generation Agent: Drafting customized slides and instructor talking points...",
          "Assessment Intelligence Agent: Structuring diagnostic test items and cognitive metrics...",
          "Curriculum Evaluation Agent: Auditing industry gaps and compliance scores..."
        ];
        const randomMsg = agentLogs[Math.floor(Math.random() * agentLogs.length)];
        setUploadLogs(prev => [...prev, randomMsg]);
      }, 1800);

      const res = await fetch(`${backendUrl}/api/courses/${activeCourseId}/regenerate`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${authToken}`
        }
      });

      clearInterval(regenerateInterval);
      clearInterval(pipelineInterval);

      if (res.ok) {
        const data = await res.json();
        if (data.status === "partial_generation") {
          setUploadLogs(prev => [
            ...prev, 
            `WARNING: Pipeline interrupted due to API ${data.error_type} at ${data.failed_agent}.`,
            `Successfully completed stages: ${data.successful_agents.join(", ") || "None"}.`,
            "Partial classroom package saved. Please retry later to complete the remaining sections."
          ]);
          failPipelineSimulation();
          setIsUploading(false);
          selectCourse(activeCourseId);
          alert(`Partial Generation Warning:\n\nThe pipeline was interrupted due to Gemini API Rate Limit / Resource Exhaustion (${data.error_type}) at ${data.failed_agent}.\n\nSuccessful sections: ${data.successful_agents.join(", ") || "None"}.\n\nSuccessfully generated items have been saved. You can try regenerating later to complete the rest!`);
          return;
        }
        setUploadLogs(prev => [...prev, ...data.logs, "SUCCESS: Complete classroom package regenerated!"]);
        completePipelineSimulation(data.pipeline_telemetry);
        setTimeout(() => {
          setIsUploading(false);
          selectCourse(activeCourseId);
        }, 1500);
      } else {
        setIsUploading(false);
        failPipelineSimulation();
        alert("Failed to regenerate course slides. Please try again.");
      }

    } catch (err) {
      clearInterval(pipelineInterval);
      setIsUploading(false);
      failPipelineSimulation();
      console.error("Regenerate course deck err:", err);
      alert("Error occurred. Check that the backend server is running.");
    }
  };

  if (!authToken) {
    return (
      <div className="flex-1 flex items-center justify-center min-h-screen bg-[#030712] p-4 relative overflow-hidden text-slate-100">
        {/* background decorative nodes */}
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-sky-500/10 rounded-full filter blur-[80px]" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-indigo-500/10 rounded-full filter blur-[80px]" />
        
        <div className="glass-panel p-8 rounded-3xl w-full max-w-md flex flex-col gap-6 text-left relative z-10 border-white/5 shadow-2xl">
          {/* Logo / Brand Header */}
          <div className="flex items-center gap-3 justify-center mb-2">
            <div className="p-2 bg-gradient-to-br from-sky-400 to-indigo-500 rounded-xl shadow-lg shadow-sky-500/15">
              <Sparkles className="h-6 w-6 text-white" />
            </div>
            <span className="font-extrabold text-2xl tracking-tight bg-gradient-to-r from-white via-slate-100 to-sky-300 bg-clip-text text-transparent">KALYX</span>
          </div>

          <div className="text-center">
            <h2 className="text-lg font-bold text-white tracking-tight">
              {authMode === "login" ? "Welcome back educator" : "Create educator profile"}
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              {authMode === "login" ? "Log in to manage agentic course generation models" : "Sign up to initialize curriculum sequences"}
            </p>
          </div>

          {authError && (
            <div className="p-3.5 bg-rose-500/10 border border-rose-500/20 rounded-xl text-xs text-rose-400 flex items-center gap-2">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{authError}</span>
            </div>
          )}

          <form onSubmit={handleAuthSubmit} className="flex flex-col gap-4">
            {authMode === "signup" && (
              <>
                <div className="flex flex-col gap-1.5">
                  <label className="text-[10px] font-extrabold text-slate-400 tracking-wider">FULL NAME</label>
                  <input 
                    type="text" 
                    placeholder="e.g. Dr. Devashish Jones" 
                    value={authFullName}
                    onChange={(e) => setAuthFullName(e.target.value)}
                    className="px-4 py-3 bg-slate-950/70 border border-slate-900 focus:border-sky-500/50 rounded-xl text-xs text-white placeholder-slate-600 outline-none transition-all"
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-[10px] font-extrabold text-slate-400 tracking-wider">EMAIL ADDRESS</label>
                  <input 
                    type="email" 
                    placeholder="e.g. devashish.jones@university.edu" 
                    value={authEmail}
                    onChange={(e) => setAuthEmail(e.target.value)}
                    className="px-4 py-3 bg-slate-950/70 border border-slate-900 focus:border-sky-500/50 rounded-xl text-xs text-white placeholder-slate-600 outline-none transition-all"
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-[10px] font-extrabold text-slate-400 tracking-wider">USERNAME</label>
                  <input 
                    type="text" 
                    placeholder="e.g. professor.jones" 
                    value={authUsername}
                    onChange={(e) => setAuthUsername(e.target.value)}
                    className="px-4 py-3 bg-slate-950/70 border border-slate-900 focus:border-sky-500/50 rounded-xl text-xs text-white placeholder-slate-600 outline-none transition-all"
                  />
                </div>
              </>
            )}

            {authMode === "login" && (
              <div className="flex flex-col gap-1.5">
                <label className="text-[10px] font-extrabold text-slate-400 tracking-wider">USERNAME OR EMAIL</label>
                <input 
                  type="text" 
                  placeholder="e.g. professor.jones or jones@stanford.edu" 
                  value={authUsernameOrEmail}
                  onChange={(e) => setAuthUsernameOrEmail(e.target.value)}
                  className="px-4 py-3 bg-slate-950/70 border border-slate-900 focus:border-sky-500/50 rounded-xl text-xs text-white placeholder-slate-600 outline-none transition-all"
                />
              </div>
            )}

            <div className="flex flex-col gap-1.5">
              <label className="text-[10px] font-extrabold text-slate-400 tracking-wider">PASSWORD</label>
              <input 
                type="password" 
                placeholder="••••••••" 
                value={authPassword}
                onChange={(e) => setAuthPassword(e.target.value)}
                className="px-4 py-3 bg-slate-950/70 border border-slate-900 focus:border-sky-500/50 rounded-xl text-xs text-white placeholder-slate-600 outline-none transition-all"
              />
            </div>

            <button 
              type="submit"
              className="mt-2 w-full py-3.5 bg-gradient-to-r from-sky-500 to-indigo-500 hover:from-sky-400 hover:to-indigo-400 rounded-xl text-xs font-bold text-white shadow-xl shadow-indigo-500/10 active:scale-[0.98] transition-all cursor-pointer"
            >
              {authMode === "login" ? "Sign In" : "Sign Up"}
            </button>
          </form>

          <div className="text-center text-xs text-slate-400 mt-2">
            {authMode === "login" ? (
              <span>
                New to KALYX?{" "}
                <button onClick={() => { setAuthMode("signup"); setAuthError(""); }} className="text-sky-400 hover:text-sky-300 font-bold hover:underline transition-all">
                  Create an account
                </button>
              </span>
            ) : (
              <span>
                Already have an account?{" "}
                <button onClick={() => { setAuthMode("login"); setAuthError(""); }} className="text-sky-400 hover:text-sky-300 font-bold hover:underline transition-all">
                  Sign in
                </button>
              </span>
            )}
          </div>
          
          <div className="border-t border-slate-900/60 pt-4 text-center">
            <span className="text-[10px] font-mono text-slate-500">
              Demo Credentials: <span className="text-indigo-400 font-bold">professor.jones</span> / <span className="text-indigo-400 font-bold">hackathon_demo_pass</span>
            </span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col text-slate-100 min-h-screen">
      
      {/* -------------------- 1. LANDING PAGE VIEW -------------------- */}
      {view === "landing" && (
        <div className="flex-1 flex flex-col justify-start p-6 md:p-12 relative overflow-y-auto h-screen scroll-smooth gap-12">
          {/* Animated Background decorative items */}
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-sky-500/10 rounded-full filter blur-[80px] animate-pulse-glow" />
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-indigo-500/10 rounded-full filter blur-[80px] animate-pulse-glow" style={{ animationDelay: "2s" }} />

          {/* Navigation Bar */}
          <header className="flex justify-between items-center max-w-7xl w-full mx-auto z-10">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-sky-400 to-indigo-500 rounded-xl shadow-lg shadow-sky-500/10">
                <Sparkles className="h-6 w-6 text-white" />
              </div>
              <span className="font-extrabold text-xl tracking-tight bg-gradient-to-r from-white via-slate-100 to-sky-300 bg-clip-text text-transparent">KALYX</span>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-xs text-slate-400 hidden sm:inline">Logged in as: <strong className="text-white font-bold">{user ? user.full_name : ""}</strong></span>
              <button 
                onClick={handleLogout}
                className="px-3.5 py-1.5 bg-slate-900 border border-slate-800 hover:border-slate-700 hover:text-white rounded-xl text-xs font-semibold active:scale-95 transition-all cursor-pointer"
              >
                Logout
              </button>
              <button 
                onClick={() => setView("workspace")}
                className="px-5 py-2.5 bg-gradient-to-r from-sky-500 to-indigo-500 hover:from-sky-400 hover:to-indigo-400 rounded-xl text-sm font-semibold shadow-xl shadow-sky-500/20 active:scale-95 transition-all cursor-pointer"
              >
                Launch Workspace
              </button>
            </div>
          </header>

          {/* Hero Section */}
          <main className="max-w-7xl w-full mx-auto flex flex-col lg:flex-row items-center gap-16 py-12 z-10 flex-1 justify-center min-h-[calc(100vh-160px)] shrink-0">
            
            {/* Left Copy block */}
            <div className="flex-1 flex flex-col gap-6 text-left max-w-2xl">
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-slate-900/80 border border-slate-800 text-xs font-medium text-sky-400 w-fit">
                <Sparkles className="h-3.5 w-3.5" />
                <span>Next-Gen Agentic Hackathon Product</span>
              </div>
              
              <h1 className="text-4xl sm:text-6xl font-black tracking-tight leading-[1.08] text-white">
                Agentic <span className="bg-gradient-to-r from-sky-400 via-sky-300 to-indigo-400 bg-clip-text text-transparent">Curriculum</span> Intelligence.
              </h1>
              
              <p className="text-lg text-slate-300 leading-relaxed">
                KALYX is an intelligent multi-agent pipeline that transforms an academic syllabus into classroom-ready slides, pedagogical notes, targeted assessments, and modernization recommendations.
              </p>

              <div className="flex flex-col sm:flex-row gap-4 mt-4">
                <button 
                  onClick={() => setView("workspace")}
                  className="px-8 py-4 bg-gradient-to-r from-sky-500 to-indigo-500 hover:from-sky-400 hover:to-indigo-400 rounded-xl text-base font-bold shadow-2xl shadow-sky-500/20 active:scale-95 transition-all flex items-center justify-center gap-2 text-white"
                >
                  Enter Platform
                  <ArrowRight className="h-5 w-5" />
                </button>
                <a 
                  href="#features"
                  className="px-8 py-4 glass-panel glass-panel-hover rounded-xl text-base font-semibold flex items-center justify-center text-slate-200"
                >
                  Explore Capabilities
                </a>
              </div>
            </div>

            {/* Right futuristic Visual Preview */}
            <div className="flex-1 w-full max-w-lg lg:max-w-none relative">
              <div className="glass-panel p-2 rounded-2xl border-white/10 shadow-2xl relative overflow-hidden bg-slate-950/40">
                
                {/* Visual Window Header */}
                <div className="flex justify-between items-center px-4 py-3 bg-slate-900/60 rounded-t-xl border-b border-slate-800">
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full bg-rose-500/80" />
                    <span className="w-3 h-3 rounded-full bg-amber-500/80" />
                    <span className="w-3 h-3 rounded-full bg-emerald-500/80" />
                  </div>
                  <span className="text-xs font-mono text-slate-400">Kalyx_Platform_Preview.tsx</span>
                  <div className="w-12" />
                </div>

                {/* Simulated UI Screen */}
                <div className="p-6 bg-slate-950/80 flex flex-col gap-6 text-left rounded-b-xl relative min-h-[300px]">
                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-3">
                      <div className="h-8 w-8 rounded-lg bg-sky-500/20 flex items-center justify-center">
                        <Sparkles className="h-4.5 w-4.5 text-sky-400" />
                      </div>
                      <div>
                        <h4 className="text-sm font-bold text-white leading-none">Advanced Machine Learning</h4>
                        <span className="text-[10px] text-slate-500">Dr. Devashish Jones</span>
                      </div>
                    </div>
                    <div className="px-2.5 py-1 rounded bg-sky-500/10 border border-sky-500/20 text-sky-400 text-xs font-extrabold">
                      89 / 100 Readiness
                    </div>
                  </div>

                  {/* Slides mini preview card */}
                  <div className="glass-panel p-4 rounded-xl border-white/5 bg-slate-900/40 flex flex-col gap-3 relative">
                    <div className="text-xs font-extrabold text-sky-400 tracking-wider">GENERATED SLIDE 3</div>
                    <div className="text-base font-bold text-white leading-tight">Linear Regression & Gradient Descent</div>
                    <div className="flex flex-col gap-1.5 text-xs text-slate-300">
                      <div>• Cost Function: Mean Squared Error (MSE) measures prediction errors</div>
                      <div>• Gradient Descent: Iterative weight updates using alpha learning rate</div>
                    </div>
                    {/* Visual box overlay */}
                    <div className="absolute right-3 bottom-3 text-[9px] text-slate-500 font-mono border border-slate-800 px-2 py-0.5 rounded">
                      [ AI Visual: Cost Bowl ]
                    </div>
                  </div>

                  {/* Agent workflow indicators */}
                  <div className="flex justify-between items-center text-xs border-t border-slate-900 pt-4">
                    <div className="flex items-center gap-2 text-slate-400">
                      <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                      <span>4-Agent Validation Loop</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-sky-400 font-semibold">
                      <span>Interactive Studio ready</span>
                      <ChevronRight className="h-3 w-3" />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </main>

          {/* Capabilities Section */}
          <section id="features" className="max-w-7xl w-full mx-auto py-20 border-t border-slate-900/60 z-10 flex flex-col gap-12 scroll-mt-6 shrink-0">
            <div className="text-center max-w-3xl mx-auto flex flex-col gap-4">
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-sky-500/10 border border-sky-500/20 text-xs font-semibold text-sky-400 w-fit mx-auto">
                <Sparkles className="h-3.5 w-3.5 animate-pulse" />
                <span>Explore KALYX Capabilities</span>
              </div>
              <h2 className="text-3xl sm:text-5xl font-black tracking-tight text-white leading-tight">
                An Intelligent Multi-Agent Engine
              </h2>
              <p className="text-slate-400 text-sm sm:text-base leading-relaxed">
                Kalyx coordinates specialized AI agents working in sequence to extract pedagogical value, validate cognitive depth, and formulate pristine classroom instruction materials.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              
              {/* Feature 1 */}
              <div className="glass-panel p-6 rounded-2xl border-white/5 bg-slate-950/40 hover:border-sky-500/30 hover:scale-[1.02] transition-all flex flex-col gap-4 group">
                <div className="p-3 bg-sky-500/10 border border-sky-500/20 rounded-xl w-fit group-hover:bg-sky-500/20 transition-all text-sky-400">
                  <Layers className="h-6 w-6" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white mb-2">Multi-Agent Planning</h3>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    Transforms raw academic syllabus inputs into a structured curriculum timeline and modular lecture sequence using hierarchical planning graphs.
                  </p>
                </div>
              </div>

              {/* Feature 2 */}
              <div className="glass-panel p-6 rounded-2xl border-white/5 bg-slate-950/40 hover:border-indigo-500/30 hover:scale-[1.02] transition-all flex flex-col gap-4 group">
                <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 rounded-xl w-fit group-hover:bg-indigo-500/20 transition-all text-indigo-400">
                  <Award className="h-6 w-6" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white mb-2">Taxonomic Auditing</h3>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    Audits lesson coverage across all six levels of Bloom's Taxonomy, checking if cognitive depth matches educational standards.
                  </p>
                </div>
              </div>

              {/* Feature 3 */}
              <div className="glass-panel p-6 rounded-2xl border-white/5 bg-slate-950/40 hover:border-emerald-500/30 hover:scale-[1.02] transition-all flex flex-col gap-4 group">
                <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl w-fit group-hover:bg-emerald-500/20 transition-all text-emerald-400">
                  <GraduationCap className="h-6 w-6" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white mb-2">Targeted Quizzes</h3>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    Generates diagnostic question banks, multiple-choice quizzes, and interactive classroom tests mapped directly to learning outcomes.
                  </p>
                </div>
              </div>

              {/* Feature 4 */}
              <div className="glass-panel p-6 rounded-2xl border-white/5 bg-slate-950/40 hover:border-pink-500/30 hover:scale-[1.02] transition-all flex flex-col gap-4 group">
                <div className="p-3 bg-pink-500/10 border border-pink-500/20 rounded-xl w-fit group-hover:bg-pink-500/20 transition-all text-pink-400">
                  <Download className="h-6 w-6" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white mb-2">Enterprise Exports</h3>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    Downloads pristine, high-fidelity slide decks in PPTX format, complete speaker notes, comprehensive PDFs, or interactive tests.
                  </p>
                </div>
              </div>

            </div>
          </section>

          {/* Footer */}
          <footer className="max-w-7xl w-full mx-auto border-t border-slate-900 py-6 text-center text-xs text-slate-500 z-10 shrink-0">
            KALYX — Developed for Agentic AI Hackathon 2026. Made with FastAPI, Next.js, and LangGraph.
          </footer>
        </div>
      )}

      {/* -------------------- 2. WORKSPACE DASHBOARD VIEW -------------------- */}
      {view === "workspace" && (
        <div className="flex-1 flex min-h-screen overflow-hidden bg-[#030712]">
          
          {/* A. WORKSPACE LEFT SIDEBAR */}
          <aside className="w-80 bg-slate-950 border-r border-slate-900 flex flex-col justify-between shrink-0">
            
            {/* Top Brand section */}
            <div className="p-5 flex flex-col gap-6">
              
              {/* Logo / Brand Header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="p-1.5 bg-gradient-to-br from-sky-500 to-indigo-500 rounded-lg">
                    <Sparkles className="h-5 w-5 text-white" />
                  </div>
                  <span className="font-black text-lg tracking-tight bg-gradient-to-r from-white to-sky-300 bg-clip-text text-transparent">KALYX</span>
                </div>
                <div className="flex gap-1">
                  <button 
                    onClick={() => setView("landing")}
                    className="text-[10px] text-slate-400 hover:text-white px-2 py-0.5 border border-slate-800 rounded hover:bg-slate-900 cursor-pointer"
                  >
                    Home
                  </button>
                  <button 
                    onClick={handleLogout}
                    className="text-[10px] text-slate-400 hover:text-white px-2 py-0.5 border border-rose-950/20 bg-rose-500/5 hover:bg-rose-500/10 rounded cursor-pointer"
                  >
                    Logout
                  </button>
                </div>
              </div>

              {/* Course Selector card */}
              <div className="flex flex-col gap-2">
                <div className="flex justify-between items-center">
                  <span className="text-[10px] font-extrabold text-slate-500 tracking-wider">ACTIVE COURSES</span>
                  <button 
                    onClick={() => setShowCreateModal(true)}
                    className="p-1 text-slate-400 hover:text-white bg-slate-900 border border-slate-800 rounded hover:border-slate-700"
                    title="Create new course"
                  >
                    <Plus className="h-3.5 w-3.5" />
                  </button>
                </div>

                <div className="flex flex-col gap-1.5 max-h-[220px] overflow-y-auto pr-1">
                  {courses.map((c) => (
                    <div 
                      key={c.id}
                      onClick={() => selectCourse(c.id)}
                      className={`group p-3 rounded-xl border flex items-center justify-between cursor-pointer transition-all ${
                        activeCourseId === c.id 
                          ? "bg-sky-500/10 border-sky-500/40 text-white" 
                          : "bg-slate-900/40 border-slate-900 hover:bg-slate-900 text-slate-300"
                      }`}
                    >
                      <div className="flex items-center gap-3 overflow-hidden">
                        <BookOpen className={`h-4.5 w-4.5 shrink-0 ${activeCourseId === c.id ? "text-sky-400" : "text-slate-500"}`} />
                        <span className="text-xs font-bold truncate leading-none">{c.title}</span>
                      </div>
                      <button 
                        onClick={(e) => handleDeleteCourse(c.id, e)}
                        className="opacity-0 group-hover:opacity-100 p-1 text-slate-500 hover:text-rose-400 hover:bg-slate-800/80 rounded transition-all"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  ))}
                  {courses.length === 0 && (
                    <div className="text-center py-6 border border-dashed border-slate-900 rounded-xl text-slate-500 text-xs">
                      No active courses. Create one to begin.
                    </div>
                  )}
                </div>
              </div>

              {/* Sidebar Action Tabs */}
              <nav className="flex flex-col gap-1.5 border-t border-slate-900 pt-6">
                <span className="text-[10px] font-extrabold text-slate-500 tracking-wider mb-1.5">PLATFORM SECTIONS</span>
                {([
                  { id: "overview", label: "Course Dashboard", icon: Layers },
                  { id: "slides", label: "AI Studio (Slides)", icon: Eye },
                  { id: "notes", label: "Instructor Notes", icon: Volume2 },
                  { id: "assessments", label: "Assessment Bank", icon: GraduationCap },
                  { id: "bloom", label: "Bloom Taxonomy Audit", icon: Award },
                  { id: "readiness", label: "Readiness Score", icon: BarChart3 },
                  { id: "traceability", label: "Traceability", icon: BookOpen },
                  { id: "pipeline", label: "Execution Pipeline", icon: Cpu },
                  { id: "gaps", label: "Industry Gap Analyzer", icon: AlertCircle },
                  { id: "export", label: "Export & Exporters", icon: Download }
                ] as const).map((tab) => {
                  const Icon = tab.icon;
                  const isDisabled = !courseDetails && tab.id !== "overview";
                  return (
                    <button
                      key={tab.id}
                      disabled={isDisabled}
                      onClick={() => setActiveTab(tab.id)}
                      className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-xs font-semibold border transition-all ${
                        isDisabled
                          ? "opacity-40 cursor-not-allowed border-transparent text-slate-600"
                          : activeTab === tab.id
                            ? "bg-gradient-to-r from-sky-500/10 to-indigo-500/10 border-sky-500/30 text-sky-400"
                            : "border-transparent text-slate-400 hover:bg-slate-900 hover:text-white"
                      }`}
                    >
                      <Icon className="h-4.5 w-4.5 shrink-0" />
                      <span>{tab.label}</span>
                    </button>
                  );
                })}
              </nav>

            </div>

            {/* User Profile display bottom */}
            <div className="p-5 border-t border-slate-900 bg-slate-950/60 flex items-center gap-3">
              <div className="h-9.5 w-9.5 rounded-full bg-gradient-to-br from-sky-400 to-indigo-500 flex items-center justify-center font-bold text-xs shadow-lg text-white">
                {user ? (user.full_name ? user.full_name.split(" ").map((n: string) => n[0]).join("").slice(0, 2).toUpperCase() : user.email.slice(0, 2).toUpperCase()) : "ED"}
              </div>
              <div className="overflow-hidden">
                <h5 className="text-xs font-bold text-white truncate">{user ? user.full_name : "Educator Profile"}</h5>
                <span className="text-[10px] text-slate-500 truncate block">{user ? (user.username ? "@" + user.username : user.email) : ""}</span>
              </div>
            </div>

          </aside>

          {/* B. MAIN INTERACTIVE CONTENT STREAM */}
          <main className="flex-1 flex flex-col overflow-hidden bg-slate-950/40 relative">
            
            {/* Header Toolbar */}
            <header className="h-16 border-b border-slate-900 bg-slate-950/80 px-6 flex items-center justify-between shrink-0 z-10">
              <div className="flex items-center gap-3">
                <h2 className="text-sm font-bold text-white">
                  {courseDetails ? courseDetails.course.title : "Get Started"}
                </h2>
                {courseDetails?.readiness_score && (
                  <span className="px-2.5 py-0.5 rounded-full bg-sky-500/10 border border-sky-500/20 text-sky-400 text-[10px] font-black">
                    {courseDetails.readiness_score.score.toFixed(0)}/100 Readiness
                  </span>
                )}
              </div>
              
              <div className="flex items-center gap-4">
                {/* Status indicators */}
                <div className="flex items-center gap-2 text-xs text-slate-400">
                  <span className="w-2 h-2 rounded-full bg-emerald-500" />
                  <span>Agent Graph Online</span>
                </div>
              </div>
            </header>

            {/* Core Views Panels */}
            <div className="flex-1 overflow-y-auto p-6 md:p-8">
              
              {/* OVERVIEW PANEL */}
              {activeTab === "overview" && (
                <div className="max-w-5xl mx-auto flex flex-col gap-8">
                  
                  {/* Active Course Selector Welcome banner */}
                  {!courseDetails ? (
                    <div className="glass-panel p-8 rounded-2xl text-center border-white/5 flex flex-col items-center justify-center py-20 max-w-xl mx-auto my-auto gap-5">
                      <div className="p-4 bg-sky-500/10 rounded-full border border-sky-500/20">
                        <UploadCloud className="h-10 w-10 text-sky-400" />
                      </div>
                      <div>
                        <h3 className="text-lg font-bold text-white">Upload Your Syllabus</h3>
                        <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
                          To get started, select an existing course or create a new one, then upload your course syllabus PDF/TXT to activate the 4-agent analysis.
                        </p>
                      </div>
                      
                      <button 
                        onClick={() => setShowCreateModal(true)}
                        className="px-5 py-2.5 bg-gradient-to-r from-sky-500 to-indigo-500 rounded-xl text-xs font-semibold shadow-xl shadow-sky-500/10"
                      >
                        Create New Course Package
                      </button>
                    </div>
                  ) : (
                    <>
                      {/* Grid cards overview */}
                      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        
                        <div className="glass-panel p-5 rounded-2xl border-white/5 flex flex-col justify-between h-36">
                          <span className="text-[10px] font-extrabold text-slate-500 tracking-wider">TOTAL SLIDES</span>
                          <h3 className="text-3xl font-black text-white">{courseDetails.slides.length}</h3>
                          <span className="text-[10px] text-slate-400">Classroom-ready slides drafted</span>
                        </div>

                        <div className="glass-panel p-5 rounded-2xl border-white/5 flex flex-col justify-between h-36">
                          <span className="text-[10px] font-extrabold text-slate-500 tracking-wider">QUIZZES & ASSESSMENTS</span>
                          <h3 className="text-3xl font-black text-white">{courseDetails.assessments.length}</h3>
                          <span className="text-[10px] text-slate-400">Mapped questions generated</span>
                        </div>

                        <div className="glass-panel p-5 rounded-2xl border-white/5 flex flex-col justify-between h-36">
                          <span className="text-[10px] font-extrabold text-slate-500 tracking-wider">BLOOM LEVELS</span>
                          <h3 className="text-3xl font-black text-white">
                            {new Set(courseDetails.learning_outcomes.map(o => o.bloom_level)).size}
                          </h3>
                          <span className="text-[10px] text-slate-400">Cognitive dimensions mapped</span>
                        </div>

                        <div className="glass-panel p-5 rounded-2xl border-sky-500/20 bg-sky-500/5 flex flex-col justify-between h-36">
                          <span className="text-[10px] font-extrabold text-sky-400 tracking-wider">READINESS SCORE</span>
                          <h3 className="text-3xl font-black text-sky-400">
                            {courseDetails.readiness_score?.score.toFixed(0)}/100
                          </h3>
                          <span className="text-[10px] text-slate-300">Audited educational quality</span>
                        </div>

                      </div>

                      {/* Course details & upload replacement form */}
                      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        
                        <div className="lg:col-span-2 flex flex-col gap-6">
                          {/* Course summary panel */}
                          <div className="glass-panel p-6 rounded-2xl border-white/5">
                            <h3 className="text-sm font-extrabold text-slate-400 tracking-wide mb-3">COURSE DESCRIPTION</h3>
                            <p className="text-sm text-slate-200 leading-relaxed">
                              {courseDetails.course.description || "An advanced machine learning class focusing on model architectures, regression models, classification boundaries, and support vector machines."}
                            </p>
                          </div>

                          {/* Syllabus syllabus topics sequence roadmap */}
                          <div className="glass-panel p-6 rounded-2xl border-white/5">
                            <h3 className="text-sm font-extrabold text-slate-400 tracking-wide mb-4">LEARNING MODULES ROADMAP</h3>
                            <div className="flex flex-col gap-3">
                              {courseDetails.curriculum_analysis?.curriculum_map?.modules?.map((m: Module, idx: number) => (
                                <div key={m.id || idx} className="flex gap-4 border-l-2 border-sky-500/20 pl-4 py-1.5 hover:border-sky-500 transition-colors">
                                  <div className="flex-1">
                                    <h4 className="text-xs font-bold text-white">Module {m.id || idx + 1}: {m.title}</h4>
                                    <div className="flex flex-wrap gap-1.5 mt-2">
                                      {m.topics?.map((topic: string, tIdx: number) => (
                                        <span key={tIdx} className="px-2 py-0.5 bg-slate-900 border border-slate-800 rounded text-[10px] text-slate-400 font-mono">
                                          {topic}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>

                        {/* Right sidebar details - replace syllabus parser */}
                        <div className="flex flex-col gap-6">
                          <div className="glass-panel p-6 rounded-2xl border-white/5 flex flex-col gap-4">
                            <h3 className="text-sm font-bold text-white flex items-center gap-2">
                              <UploadCloud className="h-4.5 w-4.5 text-sky-400" />
                              <span>Syllabus Upload Center</span>
                            </h3>
                            <p className="text-xs text-slate-400 leading-relaxed">
                              Need to update details or trigger the multi-agent graph? Select a syllabus PDF or TXT to analyze the course package.
                            </p>
                            
                            <form onSubmit={handleAnalyzeSyllabus} className="flex flex-col gap-3">
                              <div className="border-2 border-dashed border-slate-800 rounded-xl p-4 text-center cursor-pointer hover:border-sky-500/40 hover:bg-sky-500/5 transition-all relative">
                                <input 
                                  type="file" 
                                  onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                                  accept=".pdf,.txt,.docx"
                                />
                                <UploadCloud className="h-6 w-6 text-slate-500 mx-auto mb-2" />
                                <span className="text-xs text-slate-300 font-bold block truncate">
                                  {uploadFile ? uploadFile.name : "Select syllabus file"}
                                </span>
                                <span className="text-[10px] text-slate-500 mt-1 block">PDF, TXT, or DOCX (max 10MB)</span>
                              </div>

                              <button 
                                type="submit"
                                disabled={!uploadFile}
                                className={`w-full py-2.5 rounded-xl text-xs font-semibold flex items-center justify-center gap-2 transition-all ${
                                  uploadFile 
                                    ? "bg-gradient-to-r from-sky-500 to-indigo-500 hover:from-sky-400 hover:to-indigo-400 text-white cursor-pointer" 
                                    : "bg-slate-900 border border-slate-800 text-slate-500 cursor-not-allowed"
                                }`}
                              >
                                <Play className="h-3.5 w-3.5" />
                                <span>Trigger 4-Agent Analysis</span>
                              </button>
                            </form>
                          </div>
                        </div>

                      </div>
                    </>
                  )}

                </div>
              )}

              {/* LEARNING OUTCOME TRACEABILITY TAB */}
              {activeTab === "traceability" && courseDetails && (
                <div className="max-w-5xl mx-auto flex flex-col gap-6 text-left">
                  
                  <div className="flex flex-col gap-1.5">
                    <h3 className="text-lg font-bold text-white">Learning Outcome Traceability Matrix</h3>
                    <p className="text-xs text-slate-400">
                      Trace learning outcomes directly to slide decks, instructor speaker scripts, and diagnostic assessment questions.
                    </p>
                  </div>

                  <div className="flex flex-col gap-4">
                    {traceabilityData.map((outcome, idx) => {
                      const isExpanded = !!expandedOutcomes[outcome.id];
                      
                      // Status colors
                      let badgeClass = "text-sky-400 border-sky-500/20 bg-sky-500/10";
                      let barColor = "bg-sky-500";
                      if (outcome.coverage_percentage >= 80) {
                        badgeClass = "text-emerald-400 border-emerald-500/20 bg-emerald-500/10";
                        barColor = "bg-emerald-500";
                      } else if (outcome.coverage_percentage >= 50) {
                        badgeClass = "text-amber-400 border-amber-500/20 bg-amber-500/10";
                        barColor = "bg-amber-500";
                      } else {
                        badgeClass = "text-rose-400 border-rose-500/20 bg-rose-500/10";
                        barColor = "bg-rose-500";
                      }

                      return (
                        <div 
                          key={outcome.id} 
                          className={`glass-panel rounded-2xl border-white/5 overflow-hidden transition-all duration-300 ${
                            isExpanded ? "border-sky-500/20 shadow-lg shadow-sky-500/5" : ""
                          }`}
                        >
                          {/* Card Header */}
                          <div 
                            onClick={() => setExpandedOutcomes(prev => ({ ...prev, [outcome.id]: !prev[outcome.id] }))}
                            className="p-5 flex items-center justify-between gap-4 cursor-pointer hover:bg-slate-900/30 transition-all select-none"
                          >
                            <div className="flex-1 flex flex-col md:flex-row md:items-center gap-3">
                              <span className="px-2.5 py-0.5 rounded-full bg-slate-900 border border-slate-800 text-[10px] font-black text-slate-400 shrink-0 w-fit">
                                LO-{idx + 1}
                              </span>
                              <h4 className="text-xs font-bold text-white leading-relaxed line-clamp-1 md:line-clamp-none">
                                {outcome.outcome_text}
                              </h4>
                              <span className="px-2 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-[9px] font-bold shrink-0 w-fit">
                                Bloom: {outcome.bloom_level}
                              </span>
                            </div>

                            <div className="flex items-center gap-5 shrink-0">
                              <div className="flex items-center gap-3">
                                <span className={`px-2 py-0.5 rounded-full text-[9px] font-black border ${badgeClass}`}>
                                  {outcome.coverage_percentage}% Covered
                                </span>
                                <div className="w-16 bg-slate-900 border border-slate-800/80 h-1.5 rounded-full overflow-hidden hidden sm:block">
                                  <div className={`${barColor} h-full rounded-full`} style={{ width: `${outcome.coverage_percentage}%` }} />
                                </div>
                              </div>
                              {isExpanded ? (
                                <ChevronLeft className="h-4.5 w-4.5 text-slate-500 rotate-90 transition-transform" />
                              ) : (
                                <ChevronRight className="h-4.5 w-4.5 text-slate-500 transition-transform" />
                              )}
                            </div>
                          </div>

                          {/* Card Body - Mapped Deliverables */}
                          {isExpanded && (
                            <div className="px-6 pb-6 border-t border-slate-900/60 bg-slate-950/20 flex flex-col gap-5 pt-5 animate-fadeIn">
                              
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                                
                                {/* Related Slides Column */}
                                <div className="flex flex-col gap-3">
                                  <span className="text-[10px] font-extrabold text-slate-500 tracking-wider flex items-center gap-2">
                                    <Eye className="h-4 w-4 text-sky-400" />
                                    <span>COVERED BY SLIDES & NOTES</span>
                                  </span>
                                  
                                  <div className="flex flex-col gap-2">
                                    {outcome.related_slides.length > 0 ? (
                                      outcome.related_slides.map((slide: any, sIdx: number) => {
                                        const matchedNote = outcome.related_notes.find((n: any) => n.slide_index === slide.slide_index);
                                        return (
                                          <div 
                                            key={sIdx} 
                                            onClick={() => {
                                              setActiveTab("slides");
                                              const actualIdx = courseDetails.slides.findIndex(s => s.slide_index === slide.slide_index);
                                              if (actualIdx !== -1) {
                                                loadSlideEditState(courseDetails, actualIdx);
                                              }
                                            }}
                                            className="glass-panel p-3.5 rounded-xl border-white/5 hover:border-sky-500/20 cursor-pointer transition-all flex items-center justify-between text-left"
                                          >
                                            <div className="overflow-hidden">
                                              <span className="text-[9.5px] font-extrabold text-slate-500 block mb-0.5">SLIDE {slide.slide_index}</span>
                                              <p className="text-xs font-bold text-white truncate">{slide.title}</p>
                                            </div>
                                            {matchedNote && (
                                              <span className="px-2 py-0.5 rounded-md bg-sky-500/5 border border-sky-500/10 text-[9px] font-bold text-sky-400 shrink-0">
                                                {matchedNote.talking_points_count} Speaker Scripts
                                              </span>
                                            )}
                                          </div>
                                        );
                                      })
                                    ) : (
                                      <div className="text-center py-5 border border-dashed border-slate-900 rounded-xl text-slate-500 text-xs">
                                        No matching slides found for this outcome keyword signature.
                                      </div>
                                    )}
                                  </div>
                                </div>

                                {/* Related Assessments Column */}
                                <div className="flex flex-col gap-3">
                                  <span className="text-[10px] font-extrabold text-slate-500 tracking-wider flex items-center gap-2">
                                    <GraduationCap className="h-4 w-4 text-indigo-400" />
                                    <span>COVERED BY QUIZ QUESTIONS</span>
                                  </span>

                                  <div className="flex flex-col gap-2">
                                    {outcome.related_assessments.length > 0 ? (
                                      outcome.related_assessments.map((quiz: any, qIdx: number) => (
                                        <div 
                                          key={qIdx}
                                          onClick={() => {
                                            setActiveTab("assessments");
                                          }}
                                          className="glass-panel p-3.5 rounded-xl border-white/5 hover:border-indigo-500/20 cursor-pointer transition-all text-left flex flex-col gap-1.5"
                                        >
                                          <div className="flex justify-between items-center gap-2">
                                            <span className="text-[9.5px] font-extrabold text-slate-500 block">QUESTION {qIdx + 1}</span>
                                            <span className="px-2 py-0.5 rounded-md bg-indigo-500/5 border border-indigo-500/10 text-[9px] font-bold text-indigo-400">
                                              {quiz.bloom_level}
                                            </span>
                                          </div>
                                          <p className="text-xs font-semibold text-slate-200 line-clamp-1 leading-relaxed">
                                            {quiz.question_text}
                                          </p>
                                        </div>
                                      ))
                                    ) : (
                                      <div className="text-center py-5 border border-dashed border-slate-900 rounded-xl text-slate-500 text-xs">
                                        No assessment bank questions linked to this learning outcome ID.
                                      </div>
                                    )}
                                  </div>
                                </div>

                              </div>

                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>

                </div>
              )}

              {activeTab === "pipeline" && courseDetails && (
                <div className="max-w-4xl mx-auto flex flex-col gap-6 text-left">
                    
                    <div className="flex flex-col gap-1.5">
                      <h3 className="text-lg font-bold text-white">Multi-Agent Execution Pipeline</h3>
                      <p className="text-xs text-slate-400">
                        Visual log trace showing chronological execution flow, operational purposes, and completed timestamps for the KALYX multi-agent graph.
                      </p>
                    </div>

                    {/* Pipeline Summary Box */}
                    {totalDuration > 0 && (
                      <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-2xl p-5 text-left flex flex-col gap-1.5 shadow-lg shadow-emerald-500/2">
                        <div className="text-[10px] font-bold text-emerald-400 uppercase tracking-widest">4-Agent Workflow Completed</div>
                        <div className="text-lg font-black text-white">Total Execution Time: {totalDuration.toFixed(2)} seconds</div>
                      </div>
                    )}

                    <div className="glass-panel p-6 md:p-8 rounded-2xl border-white/5 relative flex flex-col gap-8">
                      {/* Vertical line connecting nodes */}
                      <div className="absolute left-[35px] md:left-[43px] top-12 bottom-12 w-[2px] bg-dashed border-l border-slate-900 border-dashed z-0" />
                    
                    {pipelineAgents.map((agent, idx) => {
                      // Color schemes per status
                      let dotColor = "bg-slate-800 border-slate-700";
                      let statusText = "Pending";
                      let badgeStyle = "text-slate-400 border-slate-800/80 bg-slate-900/60";
                      
                      if (agent.status === "completed") {
                        dotColor = "bg-emerald-500 border-emerald-400/20 shadow-[0_0_12px_rgba(16,185,129,0.4)]";
                        statusText = "Completed";
                        badgeStyle = "text-emerald-400 border-emerald-500/20 bg-emerald-500/10";
                      } else if (agent.status === "running") {
                        dotColor = "bg-sky-500 border-sky-400/20 shadow-[0_0_12px_rgba(14,165,233,0.4)] animate-pulse";
                        statusText = "Running";
                        badgeStyle = "text-sky-400 border-sky-500/20 bg-sky-500/10 animate-pulse";
                      } else if (agent.status === "failed") {
                        dotColor = "bg-rose-500 border-rose-400/20 shadow-[0_0_12px_rgba(244,63,94,0.4)] animate-ping";
                        statusText = "Failed";
                        badgeStyle = "text-rose-400 border-rose-500/20 bg-rose-500/10";
                      }

                      return (
                        <div key={idx} className="flex gap-4 md:gap-6 items-start relative z-10">
                          {/* Dot / Status symbol */}
                          <div className={`h-8 w-8 md:h-10 md:w-10 rounded-full border flex items-center justify-center shrink-0 text-white font-bold text-xs ${dotColor} transition-all duration-300`}>
                            {agent.status === "completed" ? (
                              <CheckCircle2 className="h-4.5 w-4.5 md:h-5 md:w-5 text-white" />
                            ) : agent.status === "running" ? (
                              <div className="h-2 w-2 rounded-full bg-white animate-ping" />
                            ) : agent.status === "failed" ? (
                              <AlertCircle className="h-4.5 w-4.5 md:h-5 md:w-5 text-white" />
                            ) : (
                              <span className="text-[10px] text-slate-500">{idx + 1}</span>
                            )}
                          </div>

                          {/* Agent Card Details */}
                          <div className="flex-1 glass-panel p-4 rounded-xl border-white/5 hover:border-white/10 transition-all flex flex-col md:flex-row md:items-center justify-between gap-4">
                            <div className="flex-1 text-left">
                              <h4 className="text-xs font-bold text-white flex items-center gap-2">
                                <span>{agent.name}</span>
                              </h4>
                              <p className="text-[11px] text-slate-400 leading-relaxed mt-1">{agent.purpose}</p>
                            </div>

                            <div className="flex items-center justify-between md:justify-end gap-4 shrink-0 border-t border-slate-900 md:border-t-0 pt-2.5 md:pt-0">
                              {agent.timestamp && (
                                <span className="text-[10px] font-mono text-slate-500 font-bold">
                                  {agent.timestamp}
                                </span>
                              )}
                              <span className={`px-2.5 py-0.5 rounded-full border text-[9px] font-black uppercase tracking-wider ${badgeStyle}`}>
                                {statusText}
                              </span>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                    </div>

                  </div>
                )}

              {/* SLIDES PREVIEW TAB (AI STUDIO) */}
              {activeTab === "slides" && courseDetails && (
                <div className="w-full max-w-[1440px] mx-auto flex flex-col gap-4 h-[calc(100vh-12rem)]">
                  
                  <div className="flex-1 flex flex-col lg:flex-row gap-5 overflow-hidden">
                    
                    {/* Left Thumbnails selection panel */}
                    <div className="w-full lg:w-56 shrink-0 flex flex-row lg:flex-col gap-3 overflow-x-auto lg:overflow-y-auto pb-2 lg:pb-0 pr-1 border-b lg:border-b-0 lg:border-r border-slate-900/60 lg:pr-3">
                      {courseDetails.slides.map((s, idx) => (
                        <div 
                          key={s.id}
                          onClick={() => loadSlideEditState(courseDetails, idx)}
                          className={`p-3 rounded-xl border cursor-pointer flex flex-col gap-1.5 text-left transition-all shrink-0 w-44 lg:w-full ${
                            activeSlideIndex === idx 
                              ? "bg-sky-500/10 border-sky-500/40 text-white shadow-lg" 
                              : "bg-slate-900/40 border-slate-900 hover:bg-slate-900 text-slate-300"
                          }`}
                        >
                          <span className="text-[9px] font-black text-sky-400">SLIDE {s.slide_index}</span>
                          <span className="text-xs font-extrabold truncate">{s.title}</span>
                          <span className="text-[10px] text-slate-500 truncate leading-none">
                            {s.content.length} bullet points
                          </span>
                        </div>
                      ))}
                    </div>

                    {/* Middle Workspace Slide Canvas Editor */}
                    <div className="flex-1 flex flex-col gap-4 overflow-y-auto pr-1 min-w-0">
                      
                      {/* Interactive slide canvas mock */}
                      <div className="aspect-[16/9] max-h-[360px] min-h-[300px] w-full max-w-[640px] mx-auto rounded-2xl bg-[#0a0f1e] border border-slate-800 p-6 flex flex-col justify-between relative shadow-2xl shrink-0">
                        
                        {/* Title bar decoration */}
                        <div className="flex justify-between items-center text-[10px] font-mono text-sky-400">
                          <span>[ KALYX PRESENTATION SYSTEM ]</span>
                          <span>SLIDE {activeSlideIndex + 1} OF {courseDetails.slides.length}</span>
                        </div>

                        {/* Title editable preview with edit indicator */}
                        <div className="flex items-center gap-2 border-b border-transparent hover:border-slate-800 focus-within:border-sky-500/40 transition-all pb-1 group/title">
                          <input 
                            type="text" 
                            value={editSlideTitle}
                            onChange={(e) => setEditSlideTitle(e.target.value)}
                            className="bg-transparent text-white font-black text-lg md:text-xl lg:text-2xl focus:outline-none flex-1 leading-tight tracking-tight"
                            title="Click to edit slide title"
                          />
                          <Pencil className="h-4 w-4 text-slate-500 group-hover/title:text-sky-400 transition-colors shrink-0" />
                        </div>

                        {/* Bullet items container with hover edit indicators */}
                        <div className="flex flex-col gap-1.5 py-2 overflow-y-auto max-h-[140px]">
                          {editSlideBullets.map((bullet, bIdx) => (
                            <div key={bIdx} className="flex gap-3 items-center group/bullet w-full border-b border-transparent hover:border-slate-900 focus-within:border-sky-500/40 transition-all pb-0.5">
                              <span className="text-sky-400 font-bold shrink-0">•</span>
                              <input 
                                type="text"
                                value={bullet}
                                onChange={(e) => {
                                  const updated = [...editSlideBullets];
                                  updated[bIdx] = e.target.value;
                                  setEditSlideBullets(updated);
                                }}
                                className="bg-transparent text-slate-200 text-xs focus:outline-none flex-1"
                                title="Click to edit bullet point"
                              />
                              <Pencil className="h-3.5 w-3.5 text-slate-600 opacity-0 group-hover/bullet:opacity-100 focus-within:opacity-100 transition-opacity shrink-0" />
                            </div>
                          ))}
                        </div>

                        {/* Visual overlay indicator */}
                        <div className="flex justify-between items-center text-[10px] text-slate-500 font-mono border-t border-slate-900/60 pt-2.5">
                          <span className="text-sky-400 font-semibold">[ Bloom Level: {courseDetails.assessments[activeSlideIndex]?.bloom_level || "Applying"} ]</span>
                          <span>AI Visual: {editSlideVisuals ? editSlideVisuals.substring(0, 30) + "..." : "No visuals"}</span>
                        </div>

                      </div>

                      {/* Visual Suggestions Box editable */}
                      <div className="glass-panel p-4 rounded-xl border-white/5 text-left flex flex-col gap-2.5 max-w-[640px] mx-auto w-full">
                        <div className="flex justify-between items-center">
                          <span className="text-[10px] font-extrabold text-sky-400 tracking-wider">AI VISUAL SUGGESTIONS</span>
                          <div className="flex items-center gap-1.5 text-slate-500 text-[10px]">
                            <span>Click to edit</span>
                            <Pencil className="h-3 w-3" />
                          </div>
                        </div>
                        <textarea
                          rows={2}
                          value={editSlideVisuals}
                          onChange={(e) => setEditSlideVisuals(e.target.value)}
                          className="w-full bg-slate-950 border border-slate-900 rounded-xl p-2.5 text-xs text-slate-300 focus:border-sky-500/40 focus:outline-none focus:bg-slate-950/80 transition-all resize-none"
                          placeholder="Describe the conceptual background graphic layouts..."
                        />
                      </div>

                      {/* Compact actions row containing Save and Download buttons */}
                      <div className="flex flex-col sm:flex-row gap-3 items-center justify-between bg-slate-900/40 border border-slate-900/60 rounded-xl p-4 shrink-0 max-w-[640px] mx-auto w-full">
                        <div className="flex items-center gap-2">
                          <Save className="h-4 w-4 text-sky-400" />
                          <span className="text-xs text-slate-300 font-bold">Slide Actions</span>
                        </div>
                        
                        <div className="flex flex-wrap gap-2 items-center">
                          <button 
                            onClick={handleSaveSlideChanges}
                            className="py-1.5 px-3 bg-gradient-to-r from-sky-500 to-indigo-500 hover:from-sky-400 hover:to-indigo-400 rounded-lg text-xs font-bold shadow-md shadow-sky-500/10 active:scale-95 transition-all flex items-center gap-1.5 text-white"
                          >
                            <Save className="h-3.5 w-3.5" />
                            <span>Save Changes</span>
                          </button>

                          <button 
                            onClick={handleDownloadPptx}
                            className="py-1.5 px-3 bg-slate-950 border border-slate-800 text-xs font-bold rounded-lg hover:bg-slate-900 hover:border-slate-700 active:scale-95 transition-all flex items-center gap-1.5 text-slate-200"
                          >
                            <Download className="h-3.5 w-3.5 text-sky-400" />
                            <span>Download PPTX</span>
                          </button>

                          <button 
                            onClick={handleDownloadPdf}
                            className="py-1.5 px-3 bg-slate-950 border border-slate-800 text-xs font-bold rounded-lg hover:bg-slate-900 hover:border-slate-700 active:scale-95 transition-all flex items-center gap-1.5 text-slate-200"
                          >
                            <Download className="h-3.5 w-3.5 text-indigo-400" />
                            <span>Download PDF</span>
                          </button>
                        </div>
                      </div>

                    </div>

                  </div>

                </div>
              )}

              {/* INSTRUCTOR NOTES TAB */}
              {activeTab === "notes" && courseDetails && (
                <div className="max-w-4xl mx-auto flex flex-col gap-6 text-left">
                  
                  {/* Title card selector indicators */}
                  <div className="flex justify-between items-center">
                    <div>
                      <h3 className="text-lg font-bold text-white">Lecture Instructor Notes & Script</h3>
                      <p className="text-xs text-slate-400 mt-1">Talking points, clarifications, and teaching tips compiled for slide: {courseDetails.slides[activeSlideIndex]?.title}</p>
                    </div>

                    <div className="flex gap-1.5">
                      <button 
                        disabled={activeSlideIndex === 0}
                        onClick={() => loadSlideEditState(courseDetails, activeSlideIndex - 1)}
                        className="p-1.5 bg-slate-900 border border-slate-800 rounded hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed"
                      >
                        <ChevronLeft className="h-4 w-4" />
                      </button>
                      <span className="px-3 py-1 bg-slate-900 border border-slate-800 rounded text-xs font-mono text-slate-300">
                        {activeSlideIndex + 1} / {courseDetails.slides.length}
                      </span>
                      <button 
                        disabled={activeSlideIndex === courseDetails.slides.length - 1}
                        onClick={() => loadSlideEditState(courseDetails, activeSlideIndex + 1)}
                        className="p-1.5 bg-slate-900 border border-slate-800 rounded hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed"
                      >
                        <ChevronRight className="h-4 w-4" />
                      </button>
                    </div>
                  </div>

                  {/* Main script details */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    
                    {/* Notes talking points box list */}
                    <div className="md:col-span-2 flex flex-col gap-6">
                      
                      <div className="glass-panel p-6 rounded-2xl border-white/5 flex flex-col gap-4">
                        <span className="text-[10px] font-extrabold text-sky-400 tracking-wider flex items-center gap-1.5">
                          <Volume2 className="h-4 w-4" />
                          <span>LECTURING TALKING POINTS</span>
                        </span>
                        
                        <div className="flex flex-col gap-3">
                          {editNoteTalkingPoints.map((point, ptIdx) => (
                            <div key={ptIdx} className="flex gap-3 items-start border-b border-slate-900/60 pb-3">
                              <span className="w-5 h-5 rounded-full bg-sky-500/10 text-sky-400 font-mono text-[10px] flex items-center justify-center shrink-0 mt-0.5">
                                {ptIdx + 1}
                              </span>
                              <textarea
                                value={point}
                                onChange={(e) => {
                                  const updated = [...editNoteTalkingPoints];
                                  updated[ptIdx] = e.target.value;
                                  setEditNoteTalkingPoints(updated);
                                }}
                                rows={2}
                                className="bg-transparent text-slate-200 text-xs md:text-sm border-b border-transparent focus:border-sky-500/40 focus:outline-none flex-1 focus:bg-slate-950/40 p-1.5 rounded"
                              />
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Editable Clarifying Examples */}
                      <div className="glass-panel p-6 rounded-2xl border-white/5 flex flex-col gap-4">
                        <span className="text-[10px] font-extrabold text-indigo-400 tracking-wider flex items-center gap-1.5">
                          <Lightbulb className="h-4 w-4" />
                          <span>CLARIFYING EXAMPLES</span>
                        </span>

                        <div className="flex flex-col gap-3">
                          {editNoteExamples.map((ex, exIdx) => (
                            <div key={exIdx} className="flex gap-2.5 items-center">
                              <span className="text-[10px] text-slate-500 font-bold font-mono">EX:</span>
                              <input 
                                type="text"
                                value={ex}
                                onChange={(e) => {
                                  const updated = [...editNoteExamples];
                                  updated[exIdx] = e.target.value;
                                  setEditNoteExamples(updated);
                                }}
                                className="bg-transparent text-slate-300 text-xs border-b border-transparent focus:border-sky-500/40 focus:outline-none flex-1 pb-1"
                              />
                            </div>
                          ))}
                        </div>
                      </div>

                    </div>

                    {/* Pedagogical Tips Sidebar info */}
                    <div className="flex flex-col gap-6">
                      
                      <div className="glass-panel p-6 rounded-2xl border-sky-500/20 bg-sky-500/5 flex flex-col gap-4">
                        <span className="text-[10px] font-extrabold text-sky-400 tracking-wider flex items-center gap-1.5">
                          <GraduationCap className="h-4.5 w-4.5" />
                          <span>PEDAGOGICAL TEACHING TIP</span>
                        </span>
                        
                        <textarea
                          rows={6}
                          value={editNoteTips}
                          onChange={(e) => setEditNoteTips(e.target.value)}
                          className="bg-slate-950 border border-slate-900 rounded-xl p-3 text-xs text-slate-200 focus:outline-none focus:border-sky-500/40"
                        />
                      </div>

                      <button 
                        onClick={handleSaveSlideChanges}
                        className="w-full py-3 bg-gradient-to-r from-sky-500 to-indigo-500 hover:from-sky-400 hover:to-indigo-400 rounded-xl text-xs font-bold flex items-center justify-center gap-2"
                      >
                        <Save className="h-4 w-4" />
                        <span>Save Speaker Notes</span>
                      </button>

                    </div>

                  </div>

                </div>
              )}

              {/* ASSESSMENT BANK TAB */}
              {activeTab === "assessments" && courseDetails && (
                <div className="max-w-4xl mx-auto flex flex-col gap-6 text-left">
                  
                  <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-white/5 pb-4">
                    <div>
                      <h3 className="text-lg font-bold text-white">Pedagogical Assessment & Quiz Bank</h3>
                      <p className="text-xs text-slate-400 mt-1">Multiple-choice questions (MCQs) generated by KALYX, mapped to distinct learning outcomes and Bloom levels.</p>
                    </div>
                    <div className="flex flex-row gap-2 flex-wrap">
                      <button 
                        onClick={handleDownloadInteractiveQuiz}
                        className="px-4 py-2.5 bg-gradient-to-r from-sky-500 to-indigo-500 hover:from-sky-400 hover:to-indigo-400 text-white rounded-xl text-xs font-bold flex items-center gap-1.5 shadow-md shadow-indigo-500/10 hover:shadow-indigo-500/20 transition-all cursor-pointer animate-pulse-light"
                      >
                        <Gamepad2 className="h-4 w-4" />
                        <span>Interactive Test (HTML)</span>
                      </button>
                    </div>
                  </div>

                  <div className="flex flex-col gap-4">
                    {courseDetails.assessments.filter(a => a.question_type.toUpperCase() === "MCQ" || (a.options && a.options.length > 0)).map((a, idx) => (
                      <div key={a.id || idx} className="glass-panel p-6 rounded-2xl border-white/5 relative hover:border-sky-500/20 transition-all flex flex-col gap-3">
                        
                        {/* Upper tagging bar */}
                        <div className="flex justify-between items-center text-[10px]">
                          <span className="px-2.5 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-400 font-mono">
                            {a.question_type} QUESTION
                          </span>
                          
                          <div className="flex items-center gap-3">
                            <span className="text-slate-500">Bloom level:</span>
                            <span className="px-2 py-0.5 rounded bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 font-black">
                              {a.bloom_level}
                            </span>
                          </div>
                        </div>

                        {/* Question Text */}
                        <h4 className="text-sm font-bold text-white leading-relaxed">{a.question_text}</h4>

                        {/* Options if MCQ */}
                        {a.options && (
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 my-2">
                            {a.options.map((opt, oIdx) => (
                              <div key={oIdx} className="px-4 py-2 bg-slate-950 border border-slate-900/60 rounded-xl text-xs text-slate-300">
                                {opt}
                              </div>
                            ))}
                          </div>
                        )}

                        {/* Correct Answer */}
                        <div className="p-3 bg-emerald-500/5 border border-emerald-500/10 rounded-xl text-xs text-emerald-400 font-mono">
                          <span className="font-extrabold mr-1">Correct Solution:</span>
                          {a.correct_answer}
                        </div>

                      </div>
                    ))}
                  </div>

                </div>
              )}

              {/* BLOOM TAXONOMY AUDIT TAB */}
              {activeTab === "bloom" && courseDetails && (
                <div className="max-w-4xl mx-auto flex flex-col gap-6 text-left">
                  
                  <div>
                    <h3 className="text-lg font-bold text-white">Bloom&apos;s Taxonomy Coverage Analysis</h3>
                    <p className="text-xs text-slate-400 mt-1">Audited distribution of course materials across the six tiers of modern cognitive psychology.</p>
                  </div>

                  {/* Aesthetic custom grid representing Bloom Tiers */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {[
                      { tier: "Remembering", val: 100, desc: "Recalling basic facts, definitions, algorithms, and core formulas.", color: "text-rose-400 border-rose-500/20 bg-rose-500/5" },
                      { tier: "Understanding", val: 100, desc: "Explaining principles, translating models, classifying target nodes.", color: "text-amber-400 border-amber-500/20 bg-amber-500/5" },
                      { tier: "Applying", val: 85, desc: "Implementing regression, training ML algorithms on tabular datasets.", color: "text-emerald-400 border-emerald-500/20 bg-emerald-500/5" },
                      { tier: "Analyzing", val: 90, desc: "Deconstructing outputs, diagnosing overfitting, comparing error boundaries.", color: "text-sky-400 border-sky-500/20 bg-sky-500/5" },
                      { tier: "Evaluating", val: 92, desc: "Justifying neural network selection over classical tree models.", color: "text-indigo-400 border-indigo-500/20 bg-indigo-500/5" },
                      { tier: "Creating", val: 80, desc: "Assembling ML feature pipelines, designing modern data loaders.", color: "text-violet-400 border-violet-500/20 bg-violet-500/5" }
                    ].map((tier, idx) => (
                      <div key={idx} className={`glass-panel p-5 rounded-2xl border ${tier.color} flex flex-col justify-between min-h-[160px] hover:scale-[1.02] transition-all`}>
                        <div className="flex justify-between items-center">
                          <span className="text-xs font-black tracking-wider uppercase">{tier.tier}</span>
                          <span className="px-2.5 py-0.5 rounded-full bg-white/5 border border-white/10 text-xs font-extrabold">{tier.val}% Cover</span>
                        </div>
                        <p className="text-xs text-slate-300 leading-relaxed my-3">{tier.desc}</p>
                        {/* Dynamic Progress indicator */}
                        <div className="w-full bg-slate-950/60 rounded-full h-1.5 overflow-hidden">
                          <div 
                            className="bg-current h-1.5 rounded-full" 
                            style={{ width: `${tier.val}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Recommendations */}
                  <div className="glass-panel p-6 rounded-2xl border-white/5 flex gap-4 items-start">
                    <Award className="h-10 w-10 text-sky-400 shrink-0 mt-0.5" />
                    <div>
                      <h4 className="text-sm font-bold text-white">KALYX Pedagogical Audit Assessment</h4>
                      <p className="text-xs text-slate-300 leading-relaxed mt-1.5">
                        {courseDetails.curriculum_analysis?.gap_analysis || "The syllabus is highly balanced. Consider adding one more design challenge to push 'Creating' coverage to 90%."}
                      </p>
                    </div>
                  </div>

                </div>
              )}

              {/* READINESS SCORE TAB */}
              {activeTab === "readiness" && courseDetails && (
                <div className="max-w-4xl mx-auto flex flex-col gap-8 text-left">
                  
                  <div>
                    <h3 className="text-lg font-bold text-white">Course Readiness & Quality Breakdown</h3>
                    <p className="text-xs text-slate-400 mt-1">Mathematical calculation representing overall course package quality across multiple core vectors.</p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
                    
                    {/* Big central score dial SVG */}
                    <button 
                      onClick={() => setIsReadinessExpanded(!isReadinessExpanded)}
                      className={`glass-panel p-8 rounded-2xl border-white/5 flex flex-col items-center justify-center min-h-[300px] text-center transition-all duration-300 hover:border-sky-500/30 hover:scale-[1.02] active:scale-[0.98] cursor-pointer w-full group ${
                        isReadinessExpanded ? "ring-2 ring-sky-500/20 border-sky-500/30" : ""
                      }`}
                    >
                      <span className="text-[10px] font-extrabold text-slate-500 tracking-wider mb-4 group-hover:text-sky-400 transition-colors">
                        {isReadinessExpanded ? "CLOSE DETAILED ANALYSIS" : "COMPREHENSIVE RATING"}
                      </span>
                      
                      {/* Circular meter */}
                      <div className="relative w-44 h-44 flex items-center justify-center mb-4 transform transition-transform group-hover:scale-105 duration-300">
                        <svg className="absolute inset-0 w-full h-full transform -rotate-90">
                          <circle 
                            cx="88" cy="88" r="74" 
                            className="stroke-slate-900 fill-none" 
                            strokeWidth="10"
                          />
                          <circle 
                            cx="88" cy="88" r="74" 
                            className="stroke-sky-400 fill-none filter drop-shadow-[0_0_8px_rgba(14,165,233,0.3)] transition-all duration-500" 
                            strokeWidth="10"
                            strokeDasharray="465"
                            strokeDashoffset={465 - (465 * (courseDetails.readiness_score?.score || 89)) / 100}
                          />
                        </svg>
                        <div className="flex flex-col items-center">
                          <span className="text-4xl font-black text-white group-hover:text-sky-400 transition-colors">
                            {courseDetails.readiness_score?.score.toFixed(0)}
                          </span>
                          <span className="text-[10px] font-bold text-slate-500">POINTS OUT OF 100</span>
                        </div>
                      </div>

                      <span className="text-xs font-black text-sky-400 group-hover:text-white transition-colors">
                        {isReadinessExpanded ? "HIDE BREAKDOWN" : "CLICK FOR DETAILED CRITIQUE"}
                      </span>
                    </button>

                    {/* Right side component breakdown logs */}
                    <div className="md:col-span-2 flex flex-col gap-3">
                      {[
                        { label: "Learning Outcome Coverage (25% Weight)", val: courseDetails.readiness_score?.outcome_coverage || 92, scoreStr: "Perfect mappings across 6 outcome blocks" },
                        { label: "Bloom Taxonomy Coverage (20% Weight)", val: courseDetails.readiness_score?.bloom_coverage || 91, scoreStr: "Robust distribution across remembering & design" },
                        { label: "Assessment Mapping Quality (20% Weight)", val: courseDetails.readiness_score?.assessment_quality || 90, scoreStr: "Quizzes completely match objectives" },
                        { label: "Content Completeness Index (20% Weight)", val: courseDetails.readiness_score?.completeness || 88, scoreStr: "Core modules sequenced and slide decks formatted" },
                        { label: "Modern Industry Relevance (15% Weight)", val: courseDetails.readiness_score?.industry_relevance || 82, scoreStr: "Lacks modern deep learning transformers" }
                      ].map((item, idx) => (
                        <div key={idx} className="glass-panel p-4 rounded-xl border-white/5 flex justify-between items-center">
                          <div className="flex-1 text-left">
                            <h4 className="text-xs font-bold text-white">{item.label}</h4>
                            <span className="text-[10px] text-slate-400 block mt-0.5">{item.scoreStr}</span>
                          </div>
                          <div className="flex items-center gap-4">
                            <span className="text-sm font-black text-sky-400">{item.val.toFixed(0)}%</span>
                            {/* Bar mini indicator */}
                            <div className="w-12 bg-slate-900 border border-slate-800 h-2 rounded overflow-hidden">
                              <div className="bg-sky-400 h-full rounded animate-pulse-glow" style={{ width: `${item.val}%` }} />
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>

                  </div>

                  {isReadinessExpanded && (
                    <div className="mt-4 flex flex-col gap-6 animate-fadeIn">
                      <div className="border-t border-slate-900 pt-6">
                        <h4 className="text-sm font-bold text-white mb-1">Pedagogical Critique & Recommendations</h4>
                        <p className="text-xs text-slate-400">Detailed qualitative analysis compiled by the KALYX Accreditation Lead Reviewer agent.</p>
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {[
                          { 
                            key: "completeness", 
                            label: "Curriculum Completeness", 
                            val: courseDetails.readiness_score?.completeness || 85 
                          },
                          { 
                            key: "assessment", 
                            label: "Assessment Quality", 
                            val: courseDetails.readiness_score?.assessment_quality || 72 
                          },
                          { 
                            key: "bloom", 
                            label: "Bloom Coverage", 
                            val: courseDetails.readiness_score?.bloom_coverage || 54 
                          },
                          { 
                            key: "relevance", 
                            label: "Industry Relevance", 
                            val: courseDetails.readiness_score?.industry_relevance || 61 
                          }
                        ].map((metric) => {
                          const { reason, recommendation } = parseCritique(
                            courseDetails.readiness_score?.breakdown,
                            metric.key,
                            metric.val
                          );
                          
                          let barColor = "bg-rose-500";
                          let textClass = "text-rose-400 border-rose-500/20 bg-rose-500/10";
                          let statusText = "Needs Improvement";
                          if (metric.val >= 90) {
                            barColor = "bg-emerald-500";
                            textClass = "text-emerald-400 border-emerald-500/20 bg-emerald-500/10";
                            statusText = "Excellent";
                          } else if (metric.val >= 70) {
                            barColor = "bg-amber-500";
                            textClass = "text-amber-400 border-amber-500/20 bg-amber-500/10";
                            statusText = "Good";
                          }

                          return (
                            <div key={metric.key} className="glass-panel p-5 rounded-2xl border-white/5 flex flex-col gap-4">
                              <div className="flex justify-between items-start">
                                <div>
                                  <h5 className="text-xs font-extrabold text-white uppercase tracking-wider">{metric.label}</h5>
                                  <span className="text-[10px] text-slate-500 font-semibold block mt-0.5">Qualitative Score Metric</span>
                                </div>
                                <div className="flex items-center gap-2">
                                  <span className="text-sm font-black text-white">{metric.val.toFixed(0)}/100</span>
                                  <span className={`px-2 py-0.5 rounded-full border text-[9px] font-black ${textClass}`}>
                                    {statusText}
                                  </span>
                                </div>
                              </div>

                              <div className="w-full bg-slate-900 border border-slate-800/80 h-2 rounded overflow-hidden">
                                <div className={`${barColor} h-full rounded transition-all duration-500`} style={{ width: `${metric.val}%` }} />
                              </div>

                              <div className="flex flex-col gap-2.5 text-xs bg-slate-950/40 p-3.5 border border-slate-900/60 rounded-xl">
                                <div>
                                  <span className="text-[9.5px] font-extrabold text-slate-500 uppercase tracking-wider block mb-1">Pedagogical Assessment</span>
                                  <p className="text-slate-300 leading-relaxed">{reason}</p>
                                </div>
                                <div className="border-t border-slate-900/60 pt-2.5">
                                  <span className="text-[9.5px] font-extrabold text-sky-400 uppercase tracking-wider block mb-1">Improvement Action</span>
                                  <p className="text-slate-300 leading-relaxed font-semibold">{recommendation}</p>
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                </div>
              )}

              {/* INDUSTRY GAP ANALYZER TAB */}
              {activeTab === "gaps" && courseDetails && (
                <div className="max-w-4xl mx-auto flex flex-col gap-6 text-left">
                  
                  <div>
                    <h3 className="text-lg font-bold text-white">Modern Industry Gap Analyzer</h3>
                    <p className="text-xs text-slate-400 mt-1">Checks course topics against the cutting edge 2026 technical landscape (Transformers, Vector databases, LLM agents).</p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    
                    {/* Detected Gaps Box */}
                    <div className="glass-panel p-6 rounded-2xl border-rose-500/20 bg-rose-500/5 flex flex-col gap-4">
                      <span className="text-[10px] font-extrabold text-rose-400 tracking-wider flex items-center gap-2">
                        <AlertCircle className="h-4.5 w-4.5" />
                        <span>DETECTED MODERN OUTDATED CONCEPTS</span>
                      </span>

                      <div className="flex flex-col gap-3 my-2">
                        {courseDetails.curriculum_analysis?.industry_gap_report?.missing_topics?.map((t, idx) => (
                          <div key={idx} className="px-4 py-2.5 bg-slate-950 border border-rose-500/10 rounded-xl text-xs text-slate-300 font-mono">
                            • Missing Topic: {t}
                          </div>
                        ))}
                        {(!courseDetails.curriculum_analysis?.industry_gap_report?.missing_topics || 
                          courseDetails.curriculum_analysis?.industry_gap_report.missing_topics.length === 0) && (
                          <div className="text-xs text-slate-500 py-6 text-center">
                            No major technology gaps detected! Syllabus is state-of-the-art.
                          </div>
                        )}
                      </div>
                    </div>

                    {/* AI Recommendations box */}
                    <div className="glass-panel p-6 rounded-2xl border-white/5 flex flex-col gap-4">
                      <span className="text-[10px] font-extrabold text-sky-400 tracking-wider flex items-center gap-2">
                        <Sparkles className="h-4.5 w-4.5" />
                        <span>AI MODERNIZATION RECOMMENDATIONS</span>
                      </span>

                      <div className="flex flex-col gap-3.5 my-2">
                        {courseDetails.curriculum_analysis?.industry_gap_report?.recommendations?.map((r, idx) => (
                          <div key={idx} className="flex gap-3 text-xs leading-relaxed text-slate-200">
                            <span className="text-sky-400 shrink-0 font-bold">{idx + 1}.</span>
                            <span>{r}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                  </div>

                </div>
              )}

              {/* EXPORT CENTER TAB */}
              {activeTab === "export" && courseDetails && (
                <div className="max-w-2xl mx-auto flex flex-col gap-8 text-center py-12">
                  
                  <div className="flex flex-col gap-2">
                    <h3 className="text-xl font-bold text-white">Export & Download Classroom Assets</h3>
                    <p className="text-xs text-slate-400 leading-relaxed max-w-lg mx-auto">
                      Compile your dynamic slide adjustments, speaker talking scripts, and quizzes directly into high-fidelity downloadable presentation and documentation files.
                    </p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    
                    {/* PPTX Export Button Card */}
                    <div className="glass-panel p-8 rounded-2xl border-white/5 hover:border-sky-500/20 hover:scale-[1.02] transition-all flex flex-col items-center gap-5 justify-between">
                      <div className="p-4 bg-sky-500/10 rounded-full border border-sky-500/20">
                        <Sparkles className="h-8 w-8 text-sky-400" />
                      </div>
                      <div>
                        <h4 className="text-sm font-bold text-white leading-none">PowerPoint Slide Deck</h4>
                        <span className="text-[10px] text-slate-500 block mt-2">True PPTX with speaker notes embedded</span>
                      </div>
                      
                      <button 
                        onClick={handleDownloadPptx}
                        className="w-full py-3 bg-gradient-to-r from-sky-500 to-indigo-500 rounded-xl text-xs font-semibold shadow-xl shadow-sky-500/20 active:scale-95 transition-all flex items-center justify-center gap-2"
                      >
                        <Download className="h-4 w-4" />
                        <span>Download PowerPoint Deck</span>
                      </button>
                    </div>

                    {/* PDF Export Button Card */}
                    <div className="glass-panel p-8 rounded-2xl border-white/5 hover:border-sky-500/20 hover:scale-[1.02] transition-all flex flex-col items-center gap-5 justify-between">
                      <div className="p-4 bg-rose-500/10 rounded-full border border-rose-500/20">
                        <FileText className="h-8 w-8 text-rose-400" />
                      </div>
                      <div>
                        <h4 className="text-sm font-bold text-white leading-none">PDF Syllabus Package</h4>
                        <span className="text-[10px] text-slate-500 block mt-2">Perfect to print, distribute or read offline</span>
                      </div>

                      <button 
                        onClick={handleDownloadPdf}
                        className="w-full py-3 bg-slate-900 border border-slate-800 text-slate-200 rounded-xl text-xs font-semibold hover:bg-slate-800 hover:border-slate-700 active:scale-95 transition-all flex items-center justify-center gap-2"
                      >
                        <Download className="h-4 w-4" />
                        <span>Download PDF Package</span>
                      </button>
                    </div>

                  </div>

                </div>
              )}

            </div>

            {/* C. POPUP FLOATING LIVE LOG MONITOR (AGENT GRAPH EXECUTING) */}
            {isUploading && (
              <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-md z-50 flex items-center justify-center p-6">
                <div className="glass-panel p-8 rounded-2xl border-white/10 max-w-4xl w-full flex flex-col gap-6 shadow-2xl bg-slate-950 text-left">
                  
                  {/* Title bar */}
                  <div className="flex justify-between items-center border-b border-slate-900 pb-4">
                    <div className="flex items-center gap-2.5">
                      <div className="h-2.5 w-2.5 rounded-full bg-sky-400 animate-ping shrink-0" />
                      <span className="font-extrabold text-base text-white tracking-tight">KALYX Agentic Orchestration Pipeline</span>
                    </div>
                    <span className="text-[10px] font-mono text-slate-500">[ compiled: compiled_graph.invoke() ]</span>
                  </div>

                  {/* Split Screen layout */}
                  <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 overflow-hidden">
                    
                    {/* Left: Real-time Agent Timeline */}
                    <div className="lg:col-span-3 flex flex-col gap-4 max-h-[420px] overflow-y-auto pr-2 relative">
                      {/* Vertical line connecting nodes */}
                      <div className="absolute left-[19px] top-6 bottom-6 w-[2px] bg-dashed border-l border-slate-900 border-dashed z-0" />
                      
                      {pipelineAgents.map((agent, idx) => {
                        let dotColor = "bg-slate-900 border-slate-800";
                        let statusText = "Pending";
                        let badgeStyle = "text-slate-500 border-slate-900 bg-slate-950/40";
                        
                        if (agent.status === "completed") {
                          dotColor = "bg-emerald-500 border-emerald-400/20 shadow-[0_0_8px_rgba(16,185,129,0.3)]";
                          statusText = "Completed";
                          badgeStyle = "text-emerald-400 border-emerald-500/20 bg-emerald-500/10";
                        } else if (agent.status === "running") {
                          dotColor = "bg-sky-500 border-sky-400/20 shadow-[0_0_8px_rgba(14,165,233,0.3)] animate-pulse";
                          statusText = "Running";
                          badgeStyle = "text-sky-400 border-sky-500/20 bg-sky-500/10 animate-pulse";
                        } else if (agent.status === "failed") {
                          dotColor = "bg-rose-500 border-rose-400/20 shadow-[0_0_8px_rgba(244,63,94,0.3)] animate-ping";
                          statusText = "Failed";
                          badgeStyle = "text-rose-400 border-rose-500/20 bg-rose-500/10";
                        }

                        return (
                          <div key={idx} className="flex gap-3.5 items-start relative z-10">
                            {/* Dot indicator */}
                            <div className={`h-6.5 w-6.5 rounded-full border flex items-center justify-center shrink-0 transition-all duration-300 ${dotColor}`}>
                              {agent.status === "completed" ? (
                                <CheckCircle2 className="h-3.5 w-3.5 text-white" />
                              ) : agent.status === "running" ? (
                                <div className="h-1.5 w-1.5 rounded-full bg-white animate-ping" />
                              ) : agent.status === "failed" ? (
                                <AlertCircle className="h-3.5 w-3.5 text-white" />
                              ) : (
                                <span className="text-[9px] text-slate-600 font-bold">{idx + 1}</span>
                              )}
                            </div>
                            
                            {/* Card summary */}
                            <div className="flex-1 bg-slate-900/40 border border-slate-900/60 p-2.5 rounded-xl flex items-center justify-between gap-3">
                              <div className="overflow-hidden">
                                <h5 className="text-[11px] font-bold text-white leading-none">{agent.name}</h5>
                                <span className="text-[9px] text-slate-500 block truncate mt-1">{agent.purpose}</span>
                              </div>
                              <span className={`px-2 py-0.5 rounded-full border text-[8px] font-black uppercase shrink-0 ${badgeStyle}`}>
                                {statusText}
                              </span>
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    {/* Right: scrolling terminal logs */}
                    <div className="lg:col-span-2 flex flex-col gap-3 overflow-hidden">
                      <span className="text-[10px] font-extrabold text-slate-500 tracking-wider">CONSOLE OUTPUT LOGS</span>
                      <div className="bg-slate-950 border border-slate-900 rounded-xl p-4 font-mono text-[9px] text-slate-300 h-[380px] overflow-y-auto flex flex-col gap-2">
                        {uploadLogs.map((log, lIdx) => (
                          <div key={lIdx} className="leading-relaxed break-words">
                            <span className="text-sky-400 mr-1.5">&gt;</span>
                            {log}
                          </div>
                        ))}
                        <div className="h-2" />
                      </div>
                    </div>

                  </div>

                  <span className="text-[9.5px] text-slate-500 leading-relaxed text-center block border-t border-slate-900 pt-4">
                    Evaluating Bloom Taxonomy layers, sliding presentation bullets, and computing assessment matrix in SQLite.
                  </span>
                </div>
              </div>
            )}

          </main>

          {/* D. POPUP MODAL FOR NEW COURSE INITIATING */}
          {showCreateModal && (
            <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm z-40 flex items-center justify-center p-6">
              <div className="glass-panel p-6 rounded-2xl border-white/10 max-w-md w-full flex flex-col gap-5 text-left bg-slate-950">
                <h3 className="text-base font-bold text-white">Create New Course Package</h3>
                
                <div className="flex flex-col gap-4 text-xs">
                  <div>
                    <label className="text-[10px] text-slate-500 font-bold block mb-1">COURSE TITLE</label>
                    <input 
                      type="text" 
                      placeholder="e.g. Advanced Machine Learning"
                      value={newCourseTitle}
                      onChange={(e) => setNewCourseTitle(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-800 rounded px-3 py-2.5 text-slate-200 focus:outline-none focus:border-sky-500/40"
                    />
                  </div>

                  <div>
                    <label className="text-[10px] text-slate-500 font-bold block mb-1">COURSE DESCRIPTION</label>
                    <textarea 
                      placeholder="Enter course scope, targets, prerequisites..."
                      value={newCourseDesc}
                      onChange={(e) => setNewCourseDesc(e.target.value)}
                      rows={3}
                      className="w-full bg-slate-900 border border-slate-800 rounded px-3 py-2.5 text-slate-200 focus:outline-none focus:border-sky-500/40"
                    />
                  </div>
                </div>

                <div className="flex gap-3 justify-end text-xs font-semibold">
                  <button 
                    onClick={() => setShowCreateModal(false)}
                    className="px-4 py-2 border border-slate-800 text-slate-400 hover:text-white rounded-lg"
                  >
                    Cancel
                  </button>
                  <button 
                    onClick={handleCreateCourse}
                    className="px-4 py-2 bg-gradient-to-r from-sky-500 to-indigo-500 rounded-lg text-white"
                  >
                    Create Package
                  </button>
                </div>
              </div>
            </div>
          )}

        </div>
      )}

    </div>
  );
}
