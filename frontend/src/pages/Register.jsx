import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { registerUser, getSubjects } from '../services/api';
import './Auth.css';

const Register = () => {
  const [role, setRole] = useState('student');
  const [subjects, setSubjects] = useState([]);
  const [form, setForm] = useState({
    name: '',
    email: '',
    password: '',
    roll_number: '',
    class: '',
    subject_ids: []
  });
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    const loadSubjects = async () => {
      try {
        const response = await getSubjects();
        setSubjects(response.subjects || []);
      } catch (err) {
        setSubjects([]);
      }
    };
    loadSubjects();
  }, []);

  const updateField = (key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const toggleSubject = (subjectId) => {
    setForm((prev) => {
      const exists = prev.subject_ids.includes(subjectId);
      return {
        ...prev,
        subject_ids: exists
          ? prev.subject_ids.filter((id) => id !== subjectId)
          : [...prev.subject_ids, subjectId]
      };
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');

    try {
      const payload = {
        name: form.name,
        email: form.email,
        password: form.password,
        role,
        roll_number: role === 'student' ? form.roll_number : undefined,
        class: role === 'student' ? form.class : undefined,
        subject_ids: role === 'teacher' ? form.subject_ids : []
      };
      await registerUser(payload);
      setMessage('Registration successful. You can now log in.');
    } catch (err) {
      setError(err.response?.data?.error || err.message);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1>Create Account</h1>
        {error && <div className="auth-error">{error}</div>}
        {message && <div className="auth-success">{message}</div>}
        <form onSubmit={handleSubmit} className="auth-form">
          <label>Role</label>
          <select value={role} onChange={(e) => setRole(e.target.value)}>
            <option value="student">Student</option>
            <option value="teacher">Teacher</option>
          </select>

          <label>Name</label>
          <input
            type="text"
            value={form.name}
            onChange={(e) => updateField('name', e.target.value)}
            required
          />

          <label>Email</label>
          <input
            type="email"
            value={form.email}
            onChange={(e) => updateField('email', e.target.value)}
            required
          />

          <label>Password</label>
          <input
            type="password"
            value={form.password}
            onChange={(e) => updateField('password', e.target.value)}
            required
          />

          {role === 'student' && (
            <>
              <label>Roll Number</label>
              <input
                type="text"
                value={form.roll_number}
                onChange={(e) => updateField('roll_number', e.target.value)}
                required
              />
              <label>Class</label>
              <input
                type="text"
                value={form.class}
                onChange={(e) => updateField('class', e.target.value)}
                required
              />
            </>
          )}

          {role === 'teacher' && (
            <>
              <label>Subjects (select one or more)</label>
              <div className="subject-list">
                {subjects.length === 0 && <p className="muted">No subjects available yet.</p>}
                {subjects.map((subject) => (
                  <label key={subject._id} className="subject-item">
                    <input
                      type="checkbox"
                      checked={form.subject_ids.includes(subject._id)}
                      onChange={() => toggleSubject(subject._id)}
                    />
                    {subject.name} ({subject.code}) - {subject.class}
                  </label>
                ))}
              </div>
            </>
          )}

          <button className="btn btn-primary" type="submit">Register</button>
        </form>
        <div className="auth-links">
          <Link to="/login">Already have an account? Log in</Link>
        </div>
      </div>
    </div>
  );
};

export default Register;
