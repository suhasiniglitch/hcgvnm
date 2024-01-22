package com.insurancepolicy.entity;

import java.math.BigDecimal;
import java.util.Date;

public class InsurancePolicy {

	private Long policyId;

	private String policyNumber;

	private String policyType;

	private BigDecimal premiumAmount;

	private Date startDate;

	private Date endDate;

	private boolean isActive;

	private int customerId;

	public InsurancePolicy() {
		super();
	}

	public InsurancePolicy(Long policyId, String policyNumber, String policyType, BigDecimal premiumAmount,
			Date startDate, Date endDate, boolean isActive, int customerId) {
		super();
		this.policyId = policyId;
		this.policyNumber = policyNumber;
		this.policyType = policyType;
		this.premiumAmount = premiumAmount;
		this.startDate = startDate;
		this.endDate = endDate;
		this.isActive = isActive;
		this.customerId = customerId;
	}

	public Long getPolicyId() {
		return policyId;
	}

	public void setPolicyId(Long policyId) {
		this.policyId = policyId;
	}

	public String getPolicyNumber() {
		return policyNumber;
	}

	public void setPolicyNumber(String policyNumber) {
		this.policyNumber = policyNumber;
	}

	public String getPolicyType() {
		return policyType;
	}

	public void setPolicyType(String policyType) {
		this.policyType = policyType;
	}

	public BigDecimal getPremiumAmount() {
		return premiumAmount;
	}

	public void setPremiumAmount(BigDecimal premiumAmount) {
		this.premiumAmount = premiumAmount;
	}

	public Date getStartDate() {
		return startDate;
	}

	public void setStartDate(Date startDate) {
		this.startDate = startDate;
	}

	public Date getEndDate() {
		return endDate;
	}

	public void setEndDate(Date endDate) {
		this.endDate = endDate;
	}

	public boolean isActive() {
		return isActive;
	}

	public void setActive(boolean isActive) {
		this.isActive = isActive;
	}

	public int getCustomerId() {
		return customerId;
	}

	public void setCustomerId(int customerId) {
		this.customerId = customerId;
	}

	@Override
	public String toString() {
		return "InsurancePolicy [policyId=" + policyId + ", policyNumber=" + policyNumber + ", policyType=" + policyType
				+ ", premiumAmount=" + premiumAmount + ", startDate=" + startDate + ", endDate=" + endDate
				+ ", isActive=" + isActive + ", customerId=" + customerId + "]";
	}
}
