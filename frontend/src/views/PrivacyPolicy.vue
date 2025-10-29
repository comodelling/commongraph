<template>
  <div class="container">
    <div class="privacy-policy">
      <h1>Privacy Policy</h1>
      <p class="last-updated">Last Updated: October 28, 2025</p>

      <section>
        <h2>Introduction</h2>
        <p>
          We collect minimal personal data. This policy explains what information
          we collect and how we use it.
        </p>
      </section>

      <section>
        <h2>1. Information We Collect</h2>
        <h3>Required Information</h3>
        <ul>
          <li>
            <strong>Username:</strong> A public identifier associated with all
            your edits and contributions.
          </li>
          <li>
            <strong>Password:</strong> Used for authentication. We store only a
            cryptographically hashed version - never your actual password.
          </li>
          <li>
            <strong>Security Question & Answer:</strong> Used for password
            recovery. The answer is hashed and stored securely.
          </li>
        </ul>

        <h3>Automatically Collected Information</h3>
        <ul>
          <li>
            <strong>Edit History:</strong> Timestamps and details of changes you
            make to the graph (nodes and edges).
          </li>
          <li>
            <strong>Poll Ratings & Comments:</strong> Poll ratings and comments where applicable. Ratings are anonymous.
          </li>
          <li>
            <strong>Session Data:</strong> Temporary cookies to maintain your
            login session.
          </li>
          <li>
            <strong>Server Logs:</strong> Basic technical information like IP
            addresses and access times for security and debugging purposes.
          </li>
        </ul>
      </section>

      <section>
        <h2>2. How We Use Your Information</h2>
        <ul>
          <li>
            <strong>Authentication:</strong> To verify your identity when you
            log in.
          </li>
          <li>
            <strong>Attribution:</strong> To associate your username with edits
            and contributions you make.
          </li>
          <li>
            <strong>Anonymous, aggregated polls and ratings:</strong> To provide 
            community measures to users.
          </li>
          <li>
            <strong>Account Recovery:</strong> To help you reset your password
            using your security question.
          </li>
          <li>
            <strong>Security:</strong> To protect against abuse, spam, and
            unauthorised access.
          </li>
        </ul>
      </section>

      <section>
        <h2>3. What Information is Public</h2>
        <p>
          <strong>Like Wikipedia, this is a collaborative platform where
          contributions are public.</strong>
        </p>
        <ul>
          <li>Your <strong>username</strong> is publicly visible</li>
          <li>
            All <strong>edits and contributions</strong> you make to nodes and
            edges
          </li>
          <li>
            <strong>Edit timestamps</strong> showing when you made changes
          </li>
          <li>
            <strong>Edit history</strong> showing the progression of your
            contributions
          </li>
          <li>Any <strong>comments or ratings</strong> you submit</li>
        </ul>
      </section>

      <section>
        <h2>4. What Information is Private</h2>
        <ul>
          <li>
            <strong>Password:</strong> Stored as a cryptographic hash, never in
            plain text
          </li>

          <li>
            <strong>Security Question Answer:</strong> Hashed and stored
            securely
          </li>
          <li>
            <strong>IP Address:</strong> Logged for security but not made public
          </li>
        </ul>
      </section>

      <section>
        <h2>5. Data Sharing</h2>
        <p>
          We do <strong>not sell or share</strong> your personal information
          with third parties. Your data is only processed by our hosting and
          database services necessary to operate the platform.
        </p>
        <p>
          We may disclose information if required by law or to protect the
          security and integrity of the platform.
        </p>
      </section>

      <section>
        <h2>6. Cookies</h2>
        <p>
          We use essential session cookies to keep you logged in. We do not use
          advertising cookies or third-party tracking scripts.
        </p>
      </section>

      <section>
        <h2>7. Data Retention</h2>
        <ul>
          <li>
            <strong>Active Accounts:</strong> Your account information is
            retained as long as your account is active.
          </li>
          <li>
            <strong>Edit History:</strong> For historical integrity (like
            Wikipedia), your public contributions and edit history are preserved
            even if you delete your account. This maintains the collaborative
            record of the platform's development.
          </li>
          <li>
            <strong>Deleted Accounts:</strong> When you delete your account,
            your private information (password hash, security question) is
            removed, but your username and public contributions remain for
            attribution purposes.
          </li>
        </ul>
      </section>

      <section>
        <h2>8. Your Rights</h2>
        <p>You have the right to:</p>
        <ul>
          <li><strong>Access:</strong> View your personal information</li>
          <li>
            <strong>Correct:</strong> Update your password or security question
          </li>
          <li>
            <strong>Delete:</strong> Request deletion of your account and
            private data (note: public contributions remain for historical
            integrity)
          </li>
        </ul>
        <p>
          To exercise these rights, use the account settings page or contact the
          platform administrators.
        </p>
      </section>

      <section>
        <h2>9. Security</h2>
        <p>We implement security measures including:</p>
        <ul>
          <li>
            <strong>Password Hashing:</strong> Using industry-standard bcrypt
            algorithm
          </li>
          <li><strong>HTTPS:</strong> Encrypted connections for all traffic</li>
          <li>
            <strong>Database Security:</strong> Protected access to backend
            systems
          </li>
        </ul>
        <p>
          However, no system is 100% secure. We encourage you to use strong,
          unique passwords.
        </p>
      </section>

      <section>
        <h2>10. Changes to This Policy</h2>
        <p>
          We may update this privacy policy from time to time. When we make
          significant changes, we will update the "Last Updated" date at the top
          and notify users through the platform.
        </p>
        <p>
          Continued use of the platform after changes indicates your acceptance
          of the updated policy.
        </p>
      </section>

      <section>
        <h2>11. Contact</h2>
        <p>
          If you have questions or concerns regarding this privacy policy or
          your personal data, please contact the platform administrators.
        </p>
      </section>

      <section>
        <h2>12. Your Consent</h2>
        <p>
          By creating an account and using this platform, you acknowledge that
          you have read and understood this privacy policy and agree to its
          terms.
        </p>
      </section>
    </div>
  </div>
</template>

<script>
export default {
  name: "PrivacyPolicy",
};
</script>

<style scoped>
.container {
  display: block;
  height: auto;
  min-height: 100%;
  /* padding: 2rem 1rem; */
  overflow-y: auto;
}

.privacy-policy {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
  line-height: 1.6;
}

.privacy-policy h1 {
  color: var(--color-heading);
  margin-bottom: 0.5rem;
}

.last-updated {
  color: var(--color-text-secondary);
  font-style: italic;
  margin-bottom: 2rem;
}

.privacy-policy section {
  margin-bottom: 2rem;
}

.privacy-policy h2 {
  color: var(--color-heading);
  margin-top: 2rem;
  margin-bottom: 1rem;
  border-bottom: 2px solid var(--color-border);
  padding-bottom: 0.5rem;
}

.privacy-policy h3 {
  color: var(--color-heading);
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
}

.privacy-policy ul {
  margin-left: 1.5rem;
  margin-bottom: 1rem;
}

.privacy-policy li {
  margin-bottom: 0.5rem;
}

.privacy-policy p {
  margin-bottom: 1rem;
}

.privacy-policy strong {
  color: var(--color-heading);
}
</style>
