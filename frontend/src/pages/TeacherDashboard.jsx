import React, { useEffect, useState } from 'react';
import { getCurrentUser, getSubjects, getTeacherSubmissions, evaluateSubmission, uploadModelAnswer } from '../services/api';
import './TeacherDashboard.css';

const TeacherDashboard = () => {
  const [subjects, setSubjects] = useState([]);
  const [assignedSubjectIds, setAssignedSubjectIds] = useState([]);
  const [selectedSubject, setSelectedSubject] = useState('');
  const [submissions, setSubmissions] = useState([]);
  const [modelAnswer, setModelAnswer] = useState('');
  const [modelAnswerFile, setModelAnswerFile] = useState(null);
  const [maxMarks, setMaxMarks] = useState('');
  const [question, setQuestion] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loadingModel, setLoadingModel] = useState(false);
  const [evaluatingSubmissionId, setEvaluatingSubmissionId] = useState('');

  useEffect(() => {
    const load = async () => {
      try {
        const [userRes, subjectsRes] = await Promise.all([
          getCurrentUser(),
          getSubjects()
        ]);
        const user = userRes.user || {};
        setAssignedSubjectIds(user.subject_ids || []);
        setSubjects(subjectsRes.subjects || []);
      } catch (err) {
        setError(err.response?.data?.error || err.message);
      }
    };
    load();
  }, []);

  const loadSubmissions = async (subjectId) => {
    setError('');
    setMessage('');
    try {
      const response = await getTeacherSubmissions(subjectId);
      setSubmissions(response.submissions || []);
    } catch (err) {
      setError(err.response?.data?.error || err.message);
    }
  };

  const handleSubjectChange = (value) => {
    setSelectedSubject(value);
    if (value) {
      loadSubmissions(value);
    } else {
      setSubmissions([]);
    }
  };

  const handleEvaluate = async (submissionId) => {
    setError('');
    setMessage('');
    if (!modelAnswer || !maxMarks) {
      setError('Model answer and max marks are required.');
      return;
    }

    try {
      setEvaluatingSubmissionId(submissionId);
      await evaluateSubmission(submissionId, modelAnswer, maxMarks, question);
      setMessage('Evaluation completed.');
      loadSubmissions(selectedSubject);
    } catch (err) {
      setError(err.response?.data?.error || err.message);
    } finally {
      setEvaluatingSubmissionId('');
    }
  };

  const handleModelAnswerUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    setError('');
    setMessage('');
    setLoadingModel(true);
    setModelAnswerFile(file);

    try {
      const response = await uploadModelAnswer(file);
      setModelAnswer(response.model_answer || '');
      setMessage('Model answer extracted from PDF.');
    } catch (err) {
      setError(err.response?.data?.error || err.message);
    } finally {
      setLoadingModel(false);
    }
  };

  const availableSubjects = subjects.filter((subject) => assignedSubjectIds.includes(subject._id));

  return (
    <div className="teacher-dashboard">
      <div className="teacher-container">
        <h1>Teacher Dashboard</h1>
        {error && <div className="alert error">{error}</div>}
        {message && <div className="alert success">{message}</div>}

        <section className="card">
          <h2>Select Subject</h2>
          <select value={selectedSubject} onChange={(e) => handleSubjectChange(e.target.value)}>
            <option value="">Choose subject</option>
            {availableSubjects.map((subject) => (
              <option key={subject._id} value={subject._id}>
                {subject.name} ({subject.code}) - {subject.class}
              </option>
            ))}
          </select>
        </section>

        <section className="card">
          <h2>Evaluation Setup</h2>
          <div className="form-grid">
            <div>
              <label>Question (optional)</label>
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
              />
            </div>
            <div>
              <label>Max Marks</label>
              <input
                type="number"
                value={maxMarks}
                onChange={(e) => setMaxMarks(e.target.value)}
              />
            </div>
          </div>
          <label>Upload Model Answer (PDF)</label>
          <input
            type="file"
            accept=".pdf"
            onChange={handleModelAnswerUpload}
            disabled={loadingModel}
          />
          <label>Model Answer</label>
          <textarea
            rows="5"
            value={modelAnswer}
            onChange={(e) => setModelAnswer(e.target.value)}
            placeholder="Paste model answer..."
          />
        </section>

        <section className="card">
          <h2>Pending Submissions</h2>
          {submissions.length === 0 && <p>No submissions yet.</p>}
          <div className="submission-list">
            {submissions.map((submission) => (
              <div key={submission._id} className="submission-card">
                <div>
                  <p><strong>{submission.filename}</strong></p>
                  <p className="muted">Status: {submission.status}</p>
                  {!submission.file_exists && (
                    <p className="muted">{submission.file_missing_reason || 'Submission file is missing.'}</p>
                  )}
                </div>
                <button
                  className="btn btn-primary"
                  disabled={submission.file_exists === false || evaluatingSubmissionId === submission._id}
                  onClick={() => handleEvaluate(submission._id)}
                >
                  {evaluatingSubmissionId === submission._id
                    ? 'Evaluating...'
                    : submission.status === 'evaluated'
                      ? 'Re-evaluate'
                      : 'Evaluate'}
                </button>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
};

export default TeacherDashboard;
