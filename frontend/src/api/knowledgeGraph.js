import request from '@/utils/request';

// 获取图谱数据
export const getKnowledgeGraphData = (params = {}) => {
  return request({
    url: '/api/v1/knowledge-graph/graph',
    method: 'get',
    params
  });
};

// 获取节点列表
export const getNodes = (params = {}) => {
  return request({
    url: '/api/v1/knowledge-graph/nodes',
    method: 'get',
    params
  });
};

// 获取节点详情
export const getNodeDetail = (nodeId) => {
  return request({
    url: `/api/v1/knowledge-graph/nodes/${nodeId}`,
    method: 'get'
  });
};

// 创建节点
export const createNode = (data) => {
  return request({
    url: '/api/v1/knowledge-graph/nodes',
    method: 'post',
    data
  });
};

// 更新节点
export const updateNode = (nodeId, data) => {
  return request({
    url: `/api/v1/knowledge-graph/nodes/${nodeId}`,
    method: 'put',
    data
  });
};

// 删除节点
export const deleteNode = (nodeId) => {
  return request({
    url: `/api/v1/knowledge-graph/nodes/${nodeId}`,
    method: 'delete'
  });
};

// 获取关系列表
export const getRelations = (params = {}) => {
  return request({
    url: '/api/v1/knowledge-graph/relations',
    method: 'get',
    params
  });
};

// 创建关系
export const createRelation = (data) => {
  return request({
    url: '/api/v1/knowledge-graph/relations',
    method: 'post',
    data
  });
};

// 删除关系
export const deleteRelation = (relationId) => {
  return request({
    url: `/api/v1/knowledge-graph/relations/${relationId}`,
    method: 'delete'
  });
};

// 查找知识路径
export const findPath = (params) => {
  return request({
    url: '/api/v1/knowledge-graph/path',
    method: 'get',
    params
  });
};

// 推荐文档
export const recommendDocuments = (documentId, params = {}) => {
  return request({
    url: `/api/v1/knowledge-graph/recommend/${documentId}`,
    method: 'get',
    params
  });
};
