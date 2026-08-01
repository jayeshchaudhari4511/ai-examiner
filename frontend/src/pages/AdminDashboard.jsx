import React, { useEffect, useState } from 'react';
import { createSubject, getSubjects, getPendingTeachers, approveTeacher } from '../services/api';
import './AdminDashboard.css';

const AdminDashboard = () => {
  const [subjects, setSubjects] = useState([]);
  const [pendingTeachers, setPendingTeachers] = useState([]);
  const [subjectForm, setSubjectForm] = useState({ name: '', code: '', className: '' });
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  const loadData = async () => {
    try {
      const [subjectsRes, pendingRes] = await Promise.all([
        getSubjects(),
        getPendingTeachers()
      ]);
      setSubjects(subjectsRes.subjects || []);
      setPendingTeachers(pendingRes.teachers || []);
    } catch (err) {
      setError(err.response?.data?.error || err.message);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateSubject = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');
    try {
      await createSubject(subjectForm.name, subjectForm.code, subjectForm.className);
      setSubjectForm({ name: '', code: '', className: '' });
      setMessage('Subject created.');
      loadData();
    } catch (err) {
      setError(err.response?.data?.error || err.message);
    }
  };

  const handleApproveTeacher = async (teacherId, subjectIds) => {
    setError('');
    setMessage('');
    try {
      await approveTeacher(teacherId, subjectIds);
      setMessage('Teacher approved.');
      loadData();
    } catch (err) {
      setError(err.response?.data?.error || err.message);
    }
  };

  return (
    <div className="admin-dashboard">
      <div className="admin-container">
        <h1>Admin Dashboard</h1>
        {error && <div className="alert error">{error}</div>}
        {message && <div className="alert success">{message}</div>}

        <section className="card">
          <h2>Create Subject</h2>
          <form onSubmit={handleCreateSubject} className="form-grid">
            <input
              type="text"
              placeholder="Subject name"
              value={subjectForm.name}
              onChange={(e) => setSubjectForm({ ...subjectForm, name: e.target.value })}
              required
            />
            <input
              type="text"
              placeholder="Code"
              value={subjectForm.code}
              onChange={(e) => setSubjectForm({ ...subjectForm, code: e.target.value })}
              required
            />
            <input
              type="text"
              placeholder="Class"
              value={subjectForm.className}
              onChange={(e) => setSubjectForm({ ...subjectForm, className: e.target.value })}
              required
            />
            <button className="btn btn-primary" type="submit">Create</button>
          </form>
        </section>

        <section className="card">
          <h2>Pending Teachers</h2>
          {pendingTeachers.length === 0 && <p>No pending teachers.</p>}
          <div className="pending-list">
            {pendingTeachers.map((teacher) => (
              <TeacherApproval
                key={teacher._id}
                teacher={teacher}
                subjects={subjects}
                onApprove={handleApproveTeacher}
              />
            ))}
          </div>
        </section>
      </div>
    </div>
  );
};

const TeacherApproval = ({ teacher, subjects, onApprove }) => {
  const [selected, setSelected] = useState(teacher.subject_ids || []);

  const toggleSubject = (subjectId) => {
    setSelected((prev) =>
      prev.includes(subjectId) ? prev.filter((id) => id !== subjectId) : [...prev, subjectId]
    );
  };

  return (
    <div className="pending-card">
      <div>
        <h3>{teacher.name}</h3>
        <p className="muted">{teacher.email}</p>
      </div>
      <div className="subject-pills">
        {subjects.map((subject) => (
          <label key={subject._id} className="pill">
            <input
              type="checkbox"
              checked={selected.includes(subject._id)}
              onChange={() => toggleSubject(subject._id)}
            />
            {subject.code}
          </label>
        ))}
      </div>
      <button className="btn btn-primary" onClick={() => onApprove(teacher._id, selected)}>
        Approve
      </button>
    </div>
  );
};

export default AdminDashboard;
