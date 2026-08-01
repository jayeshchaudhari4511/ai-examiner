import React, { useEffect, useState } from 'react';
import { createSubmission, getSubjects, getMyEvaluations } from '../services/api';
import './StudentDashboard.css';

const StudentDashboard = () => {
  const [subjects, setSubjects] = useState([]);
  const [selectedSubject, setSelectedSubject] = useState('');
  const [file, setFile] = useState(null);
  const [evaluations, setEvaluations] = useState([]);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    const load = async () => {
      try {
        const subjectRes = await getSubjects();
        setSubjects(subjectRes.subjects || []);
        const evalRes = await getMyEvaluations(20);
        setEvaluations(evalRes.evaluations || []);
      } catch (err) {
        setError(err.response?.data?.error || err.message);
      }
    };
    load();
  }, []);

  const subjectMap = subjects.reduce((acc, subject) => {
    acc[subject._id] = subject;
    return acc;
  }, {});

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');

    if (!selectedSubject || !file) {
      setError('Select a subject and upload your answer sheet.');
      return;
    }

    try {
      await createSubmission(file, selectedSubject);
      setMessage('Answer sheet submitted. Waiting for teacher evaluation.');
    } catch (err) {
      setError(err.response?.data?.error || err.message);
    }
  };

  return (
    <div className="student-dashboard">
      <div className="student-container">
        <h1>Student Dashboard</h1>

        <section className="card">
          <h2>Upload Answer Sheet</h2>
          {error && <div className="alert error">{error}</div>}
          {message && <div className="alert success">{message}</div>}
          <form onSubmit={handleSubmit} className="upload-form">
            <label>Subject</label>
            <select value={selectedSubject} onChange={(e) => setSelectedSubject(e.target.value)}>
              <option value="">Select subject</option>
              {subjects.map((subject) => (
                <option key={subject._id} value={subject._id}>
                  {subject.name} ({subject.code}) - {subject.class}
                </option>
              ))}
            </select>

            <label>Answer Sheet (PDF)</label>
            <input type="file" accept=".pdf" onChange={(e) => setFile(e.target.files[0])} />

            <button className="btn btn-primary" type="submit">Submit</button>
          </form>
        </section>

        <section className="card">
          <h2>Grades Card</h2>
          {evaluations.length === 0 && <p>No evaluations yet.</p>}
          <div className="grades-grid">
            {evaluations.map((evaluation) => (
              <div key={evaluation._id} className="grade-card">
                {(() => {
                  const subject = subjectMap[evaluation.subject_id];
                  const title = subject ? `${subject.name} (${subject.code})` : 'Subject';
                  const subtitle = subject ? subject.class : evaluation.student_name;
                  return (
                    <div className="grade-header">
                      <div>
                        <h3>{title}</h3>
                        <p className="muted">{subtitle}</p>
                      </div>
                      <div className="badge">{evaluation.grade}</div>
                    </div>
                  );
                })()}
                <div className="grade-stats">
                  <div>
                    <span className="label">Marks</span>
                    <strong>{evaluation.marks} / {evaluation.max_marks}</strong>
                  </div>
                  <div>
                    <span className="label">Percentage</span>
                    <strong>{evaluation.percentage}%</strong>
                  </div>
                </div>
                <div className="grade-feedback">
                  <span className="label">Feedback</span>
                  <p>{evaluation.feedback || 'No feedback yet.'}</p>
                </div>
                <div className="grade-weak">
                  <span className="label">Weak Points</span>
                  <ul>
                    {(evaluation.missing_points || []).map((point, idx) => (
                      <li key={idx}>{point}</li>
                    ))}
                    {(evaluation.missing_points || []).length === 0 && <li>None listed.</li>}
                  </ul>
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
};

export default StudentDashboard;
