// ui.test.js
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { JSDOM } from 'jsdom';
import UI from './ui';

describe('UI Class', () => {
  let ui;
  let document;
  let profileElement;

  beforeEach(() => {
    const dom = new JSDOM(`
      <div id="profile"></div>
      <div class="searchContainer">
        <div class="search"></div>
      </div>
    `);
    document = dom.window.document;
    global.document = document;
    global.window = dom.window;

    profileElement = document.getElementById('profile');
    ui = new UI();
  });

  it('should instantiate the UI class', () => {
    expect(ui).toBeDefined();
  });

  it('should clear profile element', () => {
    profileElement.innerHTML = '<div>Profile Content</div>';
    ui.clearProfile();
    expect(profileElement.innerHTML).toBe('');
  });


  it('should show alert message', () => {
    const message = 'This is an alert';
    const className = 'alert alert-danger';
    ui.showAlert(message, className);
    const alertElement = document.querySelector('.alert.alert-danger');
    expect(alertElement).toBeDefined();
    expect(alertElement.textContent).toBe(message);
  });


  it('should show profile with user data', () => {
    const user = {
      avatar_url: 'https://example.com/avatar.jpg',
      html_url: 'https://example.com',
      public_repos: 10,
      public_gists: 5,
      followers: 100,
      following: 50,
      company: 'Example Inc.',
      blog: 'https://blog.example.com',
      location: 'Earth',
      created_at: '2020-01-01'
    };
    ui.showProfile(user);
    expect(profileElement.innerHTML).toContain('https://example.com/avatar.jpg');
    expect(profileElement.innerHTML).toContain('https://example.com');
    expect(profileElement.innerHTML).toContain('Public Repos: 10');
    expect(profileElement.innerHTML).toContain('Public Gists: 5');
    expect(profileElement.innerHTML).toContain('Followers: 100');
    expect(profileElement.innerHTML).toContain('Following: 50');
    expect(profileElement.innerHTML).toContain('Company : Example Inc.');
    expect(profileElement.innerHTML).toContain('Website : https://blog.example.com');
    expect(profileElement.innerHTML).toContain('Location : Earth');
    expect(profileElement.innerHTML).toContain('Member Since : 2020-01-01');
  });

  it('should set timeout to clear alert', () => {
    vi.useFakeTimers();
    const message = 'This is an alert';
    const className = 'alert alert-danger';
    ui.showAlert(message, className);
    expect(document.querySelector('.alert.alert-danger')).toBeDefined();
    vi.runAllTimers();
    expect(document.querySelector('.alert.alert-danger')).toBeNull();
    vi.useRealTimers();
  });


  it('should clear existing alert', () => {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger';
    document.body.appendChild(alertDiv);
    ui.clearAlert();
    const currentAlert = document.querySelector('.alert');
    expect(currentAlert).toBeNull();
  });


});
