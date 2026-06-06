<template>
  <div class="sso-login-container">
    <div class="sso-card">
      <div class="sso-header">
        <h2>企业登录</h2>
        <p>选择您的企业账号登录</p>
      </div>
      
      <div class="sso-buttons">
        <el-button
          class="sso-btn dingtalk-btn"
          size="large"
          @click="redirectToDingTalk"
        >
          <span class="sso-icon">📘</span>
          <span>钉钉登录</span>
        </el-button>
        
        <el-button
          class="sso-btn wechatwork-btn"
          size="large"
          @click="redirectToWeChatWork"
        >
          <span class="sso-icon">💼</span>
          <span>企业微信登录</span>
        </el-button>
        
        <el-button
          class="sso-btn feishu-btn"
          size="large"
          @click="redirectToFeishu"
        >
          <span class="sso-icon">📱</span>
          <span>飞书登录</span>
        </el-button>
      </div>
      
      <div class="sso-divider">
        <span>或</span>
      </div>
      
      <div class="normal-login">
        <el-button
          type="primary"
          size="large"
          @click="$emit('showNormalLogin')"
        >
          账号密码登录
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const emit = defineEmits(['showNormalLogin', 'loginSuccess']);

const redirectToDingTalk = () => {
  // 构建钉钉授权URL
  const clientId = 'dingtalk_client_id'; // 需要配置实际的client_id
  const redirectUri = encodeURIComponent('http://localhost:8000/api/v1/sso/dingtalk/callback');
  const scope = 'snsapi_login';
  
  const url = `https://oapi.dingtalk.com/connect/qrconnect?appid=${clientId}&response_type=code&scope=${scope}&redirect_uri=${redirectUri}&state=STATE`;
  window.location.href = url;
};

const redirectToWeChatWork = () => {
  // 构建企业微信授权URL
  const corpid = 'wechatwork_corpid'; // 需要配置实际的corpid
  const redirectUri = encodeURIComponent('http://localhost:8000/api/v1/sso/wechatwork/callback');
  const scope = 'snsapi_base';
  
  const url = `https://open.weixin.qq.com/connect/oauth2/authorize?appid=${corpid}&redirect_uri=${redirectUri}&response_type=code&scope=${scope}&agentid=1000002&state=STATE#wechat_redirect`;
  window.location.href = url;
};

const redirectToFeishu = () => {
  // 构建飞书授权URL
  const clientId = 'feishu_client_id'; // 需要配置实际的client_id
  const redirectUri = encodeURIComponent('http://localhost:8000/api/v1/sso/feishu/callback');
  const scope = 'openid,email';
  
  const url = `https://open.feishu.cn/open-apis/authen/v1/index?redirect_uri=${redirectUri}&app_id=${clientId}&scope=${scope}&state=STATE`;
  window.location.href = url;
};
</script>

<style scoped>
.sso-login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.sso-card {
  background: #fff;
  border-radius: 16px;
  padding: 40px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
  width: 100%;
  max-width: 400px;
}

.sso-header {
  text-align: center;
  margin-bottom: 32px;
}

.sso-header h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
  color: #333;
}

.sso-header p {
  margin: 0;
  color: #999;
  font-size: 14px;
}

.sso-buttons {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.sso-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 14px 24px;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 500;
  transition: all 0.2s;
  border: none;
}

.sso-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.sso-icon {
  font-size: 24px;
}

.dingtalk-btn {
  background: linear-gradient(135deg, #26a2ff 0%, #0077ff 100%);
  color: #fff;
}

.dingtalk-btn:hover {
  background: linear-gradient(135deg, #1692ef 0%, #0067ef 100%);
}

.wechatwork-btn {
  background: linear-gradient(135deg, #07c160 0%, #06ad56 100%);
  color: #fff;
}

.wechatwork-btn:hover {
  background: linear-gradient(135deg, #06b150 0%, #059d4c 100%);
}

.feishu-btn {
  background: linear-gradient(135deg, #00bc4b 0%, #00a841 100%);
  color: #fff;
}

.feishu-btn:hover {
  background: linear-gradient(135deg, #00ac3b 0%, #009437 100%);
}

.sso-divider {
  display: flex;
  align-items: center;
  margin: 24px 0;
  color: #ccc;
  font-size: 14px;
}

.sso-divider::before,
.sso-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: #eee;
}

.sso-divider span {
  padding: 0 16px;
}

.normal-login {
  text-align: center;
}

.normal-login .el-button {
  width: 100%;
  padding: 14px 24px;
  font-size: 15px;
}
</style>
