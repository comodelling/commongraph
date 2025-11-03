<template>
  <div class="beta-notice-container">
    <div class="beta-notice">
      <div class="icon">🔒</div>
      <h1>Beta Testing Phase</h1>
      <p class="main-message">
        This platform is currently in closed beta testing.
      </p>
      <p class="details">
        You need to <router-link to="/login" class="login-link">log in</router-link> 
        to access the content and participate in the beta program.
      </p>
      <div class="cta-section">
        <p class="interested">
          Interested in participating? 
        </p>
        <p class="contact">
          Please <a href="mailto:{{ contactEmail }}" class="contact-link">contact us</a> 
          or check back later for public access!
        </p>
      </div>
      
      <div class="actions">
        <router-link to="/login" class="btn btn-primary">
          Log In
        </router-link>
        <router-link to="/signup" class="btn btn-secondary" v-if="signupEnabled">
          Request Access
        </router-link>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import { useConfig } from '../composables/useConfig';

export default {
  name: 'BetaNotice',
  setup() {
    const contactEmail = ref('contact@example.com');
    const { allowSignup, load } = useConfig();

    onMounted(async () => {
      await load();
    });

    return {
      contactEmail,
      signupEnabled: allowSignup
    };
  }
};
</script>

<style scoped>
.beta-notice-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 80px);
  padding: 20px;
  background: var(--background-color);
}

.beta-notice {
  max-width: 600px;
  width: 100%;
  background: var(--background-color);
  border: 2px solid var(--border-color);
  border-radius: 12px;
  padding: 40px;
  text-align: center;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.icon {
  font-size: 64px;
  margin-bottom: 20px;
}

h1 {
  color: var(--text-color);
  margin-bottom: 20px;
  font-size: 32px;
}

.main-message {
  font-size: 18px;
  color: var(--text-color);
  margin-bottom: 15px;
}

.details {
  font-size: 16px;
  color: var(--text-color);
  margin-bottom: 30px;
  line-height: 1.6;
}

.cta-section {
  background: var(--node-color);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 30px;
}

.interested {
  font-weight: 600;
  margin-bottom: 10px;
  color: var(--text-color);
}

.contact {
  margin: 0;
  color: var(--text-color);
}

.login-link,
.contact-link {
  color: #646cff;
  text-decoration: none;
  font-weight: 600;
}

.login-link:hover,
.contact-link:hover {
  text-decoration: underline;
}

.actions {
  display: flex;
  gap: 15px;
  justify-content: center;
  flex-wrap: wrap;
}

.btn {
  padding: 12px 30px;
  border-radius: 6px;
  text-decoration: none;
  font-weight: 600;
  font-size: 16px;
  transition: all 0.3s ease;
  display: inline-block;
}

.btn-primary {
  background-color: #646cff;
  color: white !important;
}

.btn-primary:hover {
  background-color: #535bf2;
  transform: translateY(-2px);
  color: white !important;
}

.btn-secondary {
  background-color: transparent;
  color: #646cff;
  border: 2px solid #646cff;
}

.btn-secondary:hover {
  background-color: #646cff;
  color: white !important;
}

@media (max-width: 768px) {
  .beta-notice {
    padding: 30px 20px;
  }

  h1 {
    font-size: 24px;
  }

  .main-message {
    font-size: 16px;
  }

  .actions {
    flex-direction: column;
  }

  .btn {
    width: 100%;
  }
}
</style>
